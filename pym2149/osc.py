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
from pyrbo import turbo
from const import u4

class DerivativeNode(BufNode):

    def __init__(self):
        BufNode.__init__(self, derivativedtype)

    def reset(self, shape):
        self.ringcursor = shape.newcursor()
        self.resetprogress()
        return self

    def swapring(self, shape):
        self.ringcursor.swapring(shape)

    def hold(self, signalbuf):
        signalbuf.fill_same(self.ringcursor.contextdc())

    def integral(self, signalbuf):
        signalbuf.integrate(self.blockbuf)

class SimpleDerivative(DerivativeNode):

    def __init__(self, scaleofstep, periodreg, eagerstepsize):
        DerivativeNode.__init__(self)
        self.scaleofstep = scaleofstep
        self.periodreg = periodreg
        self.eagerstepsize = eagerstepsize

    def resetprogress(self):
        self.progress = 0

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

    indexdtype = np.int64 # Must be signed and this big, at least for the tests.
    singleton0 = np.zeros(1, dtype = indexdtype)

    def __init__(self, chipimplclock, timer):
        DerivativeNode.__init__(self)
        self.indices = MasterBuf(self.indexdtype)
        self.effectversion = None
        self.chipimplclock = chipimplclock
        self.timer = timer

    def resetprogress(self):
        self.prescalercount = None # Timer was stopped.
        self.maincounter = 0 # Force reload.

    def callimpl(self):
        if self.effectversion != self.timer.effect.version:
            self.reset(self.timer.effect.value.getshape())
            self.effectversion = self.timer.effect.version
        else:
            self.swapring(self.timer.effect.value.getshape())
        prescaler = self.timer.prescalerornone.value
        voidinterrupt = (0 == self.prescalercount) and not self.maincounter
        if prescaler is None:
            if voidinterrupt:
                # There was an interrupt in the void:
                self.ringcursor.putindexed(self.blockbuf, self.singleton0)
                action = self.integral
                self.maincounter = 0 # Reload on restart.
            else:
                action = self.hold
                # In this case we preserve maincounter value.
            self.prescalercount = None
        else:
            maxprescaler = prescaler * self.chipimplclock
            etdr = self.timer.effectivedata.value
            stepsize = maxprescaler * etdr
            if voidinterrupt:
                stepindex = 0
            else:
                if self.prescalercount is None:
                    self.prescalercount = maxprescaler
                stepindex = self.prescalercount + (self.maincounter - 1) * maxprescaler
                if ceildiv(stepindex, mfpclock) < 0:
                    stepindex = 0
            if ceildiv(stepindex, mfpclock) >= self.block.framecount:
                action = self.hold
                remaining = self.prescalercount + (self.maincounter - 1) * maxprescaler - self.block.framecount * mfpclock
            else:
                stepcount = ((self.block.framecount - 1) * mfpclock - stepindex) // stepsize + 1
                indices = self.indices.ensureandcrop(stepcount)
                self.prepareindices(stepcount, indices.buf, stepsize, stepindex, mfpclock)
                # Note values can integrate to 2 if there was an overflow earlier.
                self.ringcursor.putindexed(self.blockbuf, indices.buf) # XXX: Copy to int32 for the indexing?
                action = self.integral
                lastindex = (stepcount - 1) * stepsize + stepindex
                remaining = etdr * maxprescaler - (self.block.framecount * mfpclock - lastindex)
            self.prescalercount = remaining % maxprescaler
            # TODO: Unit-test this is the correct logic.
            self.maincounter = (remaining+maxprescaler-1) // maxprescaler
        return action

    @turbo(self = {}, i = u4, n = u4, indices = [np.int64], stepsize = np.int64, stepindex = np.int64, value = np.int64, mfpclock = np.int64)
    def prepareindices(self, n, indices, stepsize, stepindex, mfpclock):
        value = stepindex + mfpclock - 1
        for i in xrange(n):
            indices[i] = value // mfpclock
            value += stepsize

class IntegralNode(BufNode):

    def __init__(self, derivative):
        BufNode.__init__(self, signaldtype) # Sinus effect is in [0, 15] so dtype must support that.
        self.derivative = derivative

    def callimpl(self):
        self.chain(self.derivative)(self.blockbuf)

class RToneOsc(IntegralNode):

    def __init__(self, chipimplclock, timer):
        IntegralNode.__init__(self, RationalDerivative(chipimplclock, timer))

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
