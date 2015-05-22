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

import lfsr, itertools, numpy as np
from nod import BufNode
from buf import DerivativeRing, MasterBuf, derivativedtype, signaldtype
from mfp import mfpclock
from shapes import cycle, tonediffs

class DerivativeNode(BufNode):

    def __init__(self):
        BufNode.__init__(self, derivativedtype)

    def reset(self, derivativering):
        if derivativering.buf.dtype != self.dtype:
            raise Exception('Ring must have same dtype as this.')
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
            self.blockbuf.fill(0)
            stepcount = (self.block.framecount - stepindex + self.stepsize - 1) // self.stepsize
            self.ringcursor.putstrided(self.blockbuf, stepindex, self.stepsize, stepcount)
            self.progress = (self.block.framecount - stepindex) % self.stepsize
            return self.integral

def ceildiv(numerator, denominator):
    return -((-numerator) // denominator)

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
                self.blockbuf.fill(0)
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
            self.blockbuf.fill(0)
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
        self.diff = derivative

class RToneOsc(IntegralNode):

    def __init__(self, chipimplclock, timer):
        IntegralNode.__init__(self, RationalDerivative(chipimplclock, timer))
        self.effectversion = None
        self.effectreg = timer.effect

    def callimpl(self):
        if self.effectversion != self.effectreg.version:
            self.diff.reset(self.effectreg.value.diffs)
            self.effectversion = self.effectreg.version
        self.chain(self.diff)(self.blockbuf)

class ToneOsc(IntegralNode):

    def __init__(self, scale, periodreg):
        scaleofstep = scale * 2 // 2 # Normally half of 16.
        IntegralNode.__init__(self, SimpleDerivative(scaleofstep, periodreg, True).reset(tonediffs))

    def callimpl(self):
        self.chain(self.diff)(self.blockbuf)

class NoiseDiffs(DerivativeRing):

    def __init__(self, nzdegrees):
        DerivativeRing.__init__(self, lfsr.Lfsr(nzdegrees))

class NoiseOsc(IntegralNode):

    def __init__(self, scale, periodreg, noisediffs):
        scaleofstep = scale * 2 # This results in authentic spectrum, see qnoispec.
        IntegralNode.__init__(self, SimpleDerivative(scaleofstep, periodreg, False).reset(noisediffs))

    def callimpl(self):
        self.chain(self.diff)(self.blockbuf)

class EnvOsc(IntegralNode):

    steps = 32
    diffs0c = DerivativeRing(cycle(range(steps)))
    diffs08 = DerivativeRing(cycle(range(steps - 1, -1, -1)))
    diffs0e = DerivativeRing(cycle(range(steps) + range(steps - 1, -1, -1)))
    diffs0a = DerivativeRing(cycle(range(steps - 1, -1, -1) + range(steps)))
    diffs0f = DerivativeRing(itertools.chain(xrange(steps), cycle([0])), steps)
    diffs0d = DerivativeRing(itertools.chain(xrange(steps), cycle([steps - 1])), steps)
    diffs0b = DerivativeRing(itertools.chain(xrange(steps - 1, -1, -1), cycle([steps - 1])), steps)
    diffs09 = DerivativeRing(itertools.chain(xrange(steps - 1, -1, -1), cycle([0])), steps)

    def __init__(self, scale, periodreg, shapereg):
        scaleofstep = scale * 32 // self.steps
        IntegralNode.__init__(self, SimpleDerivative(scaleofstep, periodreg, True))
        self.shapeversion = None
        self.shapereg = shapereg

    def callimpl(self):
        if self.shapeversion != self.shapereg.version:
            shape = self.shapereg.value
            if shape == (shape & 0x07):
                shape = (0x09, 0x0f)[bool(shape & 0x04)]
            self.diff.reset(getattr(self, "diffs%02x" % shape))
            self.shapeversion = self.shapereg.version
        self.chain(self.diff)(self.blockbuf)
