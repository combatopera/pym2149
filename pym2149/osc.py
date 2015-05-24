# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

import itertools, numpy as np
from nod import BufNode
from ring import DerivativeRing, derivativedtype, signaldtype
from buf import MasterBuf
from mfp import mfpclock
from shapes import toneshape
from util import ceildiv

class DerivativeNode(BufNode):

    def __init__(self):
        BufNode.__init__(self, derivativedtype)

    def reset(self, derivativering):
        self.ringcursor = derivativering.newcursor()
        self.progress = 0
        return self

    def hold(self, signalbuf):
        signalbuf.fill(self.ringcursor.contextdc())

    def integral(self, signalbuf):
        signalbuf.integrate(self.blockbuf)

class SimpleDerivative(DerivativeNode):

    def __init__(self, scaleofstep, periodreg, eagerstepsize):
        DerivativeNode.__init__(self)
        self.scaleofstep = scaleofstep
        self.periodreg = periodreg
        self.eagerstepsize = eagerstepsize

    def updatestepsize(self, eager):
        if eager == self.eagerstepsize:
            self.stepsize = self.scaleofstep * self.periodreg.value

    def callimpl(self):
        self.updatestepsize(True)
        if not self.progress:
            stepindex = 0
        else:
            # If progress beats the new stepsize, we step right away:
            stepindex = max(0, self.stepsize - self.progress)
        if stepindex >= self.block.framecount:
            # Next step of waveform is beyond this block:
            self.progress += self.block.framecount
            return self.hold
        else:
            self.updatestepsize(False)
            stepcount = (self.block.framecount - stepindex + self.stepsize - 1) // self.stepsize
            self.ringcursor.putstrided(self.blockbuf, stepindex, self.stepsize, stepcount)
            self.progress = (self.block.framecount - stepindex) % self.stepsize
            return self.integral

class RationalDerivative(DerivativeNode):

    singleton0 = np.zeros(1, dtype = np.int32)

    def __init__(self, chipimplclock, timer):
        DerivativeNode.__init__(self)
        self.indices = MasterBuf(np.int64) # Must be signed and this big, at least for the tests.
        self.chipimplclock = chipimplclock
        self.timer = timer

    def callimpl(self):
        if not self.timer.isrunning():
            if not self.progress:
                self.ringcursor.putindexed(self.blockbuf, self.singleton0)
                self.progress = self.block.framecount * mfpclock
                return self.integral
            else:
                self.progress += self.block.framecount * mfpclock
                return self.hold
        stepsize = self.timer.getstepsize() * self.chipimplclock
        if 0 == self.progress:
            stepindex = 0
        else:
            stepindex = stepsize - self.progress
            if ceildiv(stepindex, mfpclock) < 0:
                stepindex = 0
        if ceildiv(stepindex, mfpclock) >= self.block.framecount:
            self.progress += self.block.framecount * mfpclock
            return self.hold
        else:
            stepcount = ((self.block.framecount - 1) * mfpclock - stepindex) // stepsize + 1
            indices = self.indices.ensureandcrop(stepcount)
            indices.arange(-stepsize)
            indices.add(-stepindex)
            indices.ceildiv(mfpclock, alreadynegated = True)
            # Note values can integrate to 2 if there was an overflow earlier.
            self.ringcursor.putindexed(self.blockbuf, indices.buf) # XXX: Copy to int32 for the indexing?
            self.progress = self.block.framecount * mfpclock - (stepcount - 1) * stepsize - stepindex
            if self.progress == stepsize:
                self.progress = 0
            return self.integral

class IntegralNode(BufNode):

    def __init__(self, derivative):
        BufNode.__init__(self, signaldtype) # Sinus effect is in [0, 15] so dtype must support that.
        self.derivative = derivative

    def callimpl(self):
        self.chain(self.derivative)(self.blockbuf)

class RToneOsc(IntegralNode):

    def __init__(self, chipimplclock, timer):
        IntegralNode.__init__(self, RationalDerivative(chipimplclock, timer))
        self.effectversion = None
        self.effectreg = timer.effect

    def callimpl(self):
        if self.effectversion != self.effectreg.version:
            self.derivative.reset(self.effectreg.value.diffs)
            self.effectversion = self.effectreg.version
        IntegralNode.callimpl(self)

class ToneOsc(IntegralNode):

    def __init__(self, scale, periodreg):
        scaleofstep = scale * 2 // 2 # Normally half of 16.
        IntegralNode.__init__(self, SimpleDerivative(scaleofstep, periodreg, True).reset(toneshape))

class NoiseOsc(IntegralNode):

    def __init__(self, scale, periodreg, noiseshape):
        scaleofstep = scale * 2 # This results in authentic spectrum, see qnoispec.
        IntegralNode.__init__(self, SimpleDerivative(scaleofstep, periodreg, False).reset(noiseshape))

class EnvOsc(IntegralNode):

    steps = 32
    shapes = {
        0x0c: DerivativeRing(xrange(steps)),
        0x08: DerivativeRing(xrange(steps - 1, -1, -1)),
        0x0e: DerivativeRing(itertools.chain(xrange(steps), xrange(steps - 1, -1, -1))),
        0x0a: DerivativeRing(itertools.chain(xrange(steps - 1, -1, -1), xrange(steps))),
        0x0f: DerivativeRing(itertools.chain(xrange(steps), [0]), steps),
        0x0d: DerivativeRing(itertools.chain(xrange(steps), [steps - 1]), steps),
        0x0b: DerivativeRing(itertools.chain(xrange(steps - 1, -1, -1), [steps - 1]), steps),
        0x09: DerivativeRing(itertools.chain(xrange(steps - 1, -1, -1), [0]), steps),
    }
    for s in xrange(0x08):
        shapes[s] = shapes[0x0f if s & 0x04 else 0x09]
    del s

    def __init__(self, scale, periodreg, shapereg):
        scaleofstep = scale * 32 // self.steps
        IntegralNode.__init__(self, SimpleDerivative(scaleofstep, periodreg, True))
        self.shapeversion = None
        self.shapereg = shapereg

    def callimpl(self):
        if self.shapeversion != self.shapereg.version:
            self.derivative.reset(self.shapes[self.shapereg.value])
            self.shapeversion = self.shapereg.version
        IntegralNode.callimpl(self)
