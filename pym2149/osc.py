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

import numpy as np
from nod import BufNode
from ring import derivativedtype, signaldtype
from buf import MasterBuf
from util import ceildiv
from pyrbo import turbo, LOCAL
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

class RationalDerivative(DerivativeNode):

    indexdtype = np.int64 # Must be signed and this big, at least for the tests.
    singleton0 = np.zeros(1, dtype = indexdtype)

    def __init__(self, mfpclock, chipimplclock, timer):
        DerivativeNode.__init__(self)
        self.indices = MasterBuf(self.indexdtype)
        self.effectversion = None
        self.mfpclock = mfpclock
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
                if ceildiv(stepindex, self.mfpclock) < 0:
                    stepindex = 0
            if ceildiv(stepindex, self.mfpclock) >= self.block.framecount:
                action = self.hold
                remaining = self.prescalercount + (self.maincounter - 1) * maxprescaler - self.block.framecount * self.mfpclock
            else:
                stepcount = ((self.block.framecount - 1) * self.mfpclock - stepindex) // stepsize + 1
                indices = self.indices.ensureandcrop(stepcount)
                self.prepareindices(stepcount, indices.buf, stepsize, stepindex)
                # Note values can integrate to 2 if there was an overflow earlier.
                self.ringcursor.putindexed(self.blockbuf, indices.buf) # XXX: Copy to int32 for the indexing?
                action = self.integral
                lastindex = (stepcount - 1) * stepsize + stepindex
                remaining = etdr * maxprescaler - (self.block.framecount * self.mfpclock - lastindex)
            self.prescalercount = remaining % maxprescaler
            # TODO: Unit-test this is the correct logic.
            self.maincounter = (remaining+maxprescaler-1) // maxprescaler
        return action

    @turbo(self = dict(mfpclock = np.int64), i = u4, n = u4, indices = [np.int64], stepsize = np.int64, stepindex = np.int64, value = np.int64)
    def prepareindices(self, n, indices, stepsize, stepindex):
        self_mfpclock = LOCAL
        value = stepindex + self_mfpclock - 1
        for i in xrange(n):
            indices[i] = value // self_mfpclock
            value += stepsize

class IntegralNode(BufNode):

    def __init__(self, derivative):
        BufNode.__init__(self, signaldtype) # Sinus effect is in [0, 15] so dtype must support that.
        self.derivative = derivative

    def callimpl(self):
        self.chain(self.derivative)(self.blockbuf)

class RToneOsc(IntegralNode):

    def __init__(self, mfpclock, chipimplclock, timer):
        IntegralNode.__init__(self, RationalDerivative(mfpclock, chipimplclock, timer))
