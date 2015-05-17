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

from __future__ import division
import lfsr, itertools, math, numpy as np
from nod import BufNode
from dac import level5toamp, amptolevel5
from buf import DiffRing, RingCursor, MasterBuf
from mfp import mfpclock
from shapes import cycle, tonediffs

class BinDiff(BufNode):

    def __init__(self, dtype):
        BufNode.__init__(self, dtype)

    def reset(self, diffs):
        self.ringcursor = RingCursor(diffs)
        self.progress = 0
        return self

    def hold(self, signalbuf):
        signalbuf.fill(self.ringcursor.currentdc())

    def integral(self, signalbuf):
        signalbuf.integrate(self.blockbuf)

class OscDiff(BinDiff):

    def __init__(self, dtype, scaleofstep, periodreg, eagerstepsize):
        BinDiff.__init__(self, dtype)
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
            dc = self.ringcursor.currentdc()
            self.ringcursor.put(self.blockbuf, stepindex, self.stepsize, stepcount)
            self.blockbuf.addtofirst(dc) # Add last value of previous integral.
            self.progress = (self.block.framecount - stepindex) % self.stepsize
            return self.integral

def ceildiv(numerator, denominator):
    return -((-numerator) // denominator)

class RationalDiff(BinDiff):

    singleton0 = np.zeros(1, dtype = np.int32)

    def __init__(self, dtype, chipimplclock, timer):
        BinDiff.__init__(self, dtype)
        self.indices = MasterBuf(np.int64) # Must be signed and this big, at least for the tests.
        self.chipimplclock = chipimplclock
        self.timer = timer

    def callimpl(self):
        if not self.timer.isrunning():
            if not self.progress:
                self.blockbuf.fill(0)
                dc = self.ringcursor.currentdc()
                self.ringcursor.put2(self.blockbuf, self.singleton0)
                self.blockbuf.addtofirst(dc)
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
            dc = self.ringcursor.currentdc()
            # Note values can integrate to 2 if there was an overflow earlier.
            self.ringcursor.put2(self.blockbuf, indices.buf) # XXX: Copy to int32 for the indexing?
            self.blockbuf.addtofirst(dc)
            self.progress = self.block.framecount * mfpclock - (stepcount - 1) * stepsize - stepindex
            if self.progress == stepsize:
                self.progress = 0
            return self.integral

class RToneOsc(BufNode):

    def __init__(self, chipimplclock, timer):
        BufNode.__init__(self, self.zto255dtype) # Sinus effect is in [0, 15] so dtype must support that.
        self.diff = RationalDiff(self.zto127diffdtype, chipimplclock, timer)
        self.effectversion = None
        self.effectreg = timer.effect

    def callimpl(self):
        if self.effectversion != self.effectreg.version:
            self.diff.reset(self.effectreg.value.diffs)
            self.effectversion = self.effectreg.version
        self.chain(self.diff)(self.blockbuf)

class ToneOsc(BufNode):

    def __init__(self, scale, periodreg):
        BufNode.__init__(self, self.binarydtype)
        scaleofstep = scale * 2 // 2 # Normally half of 16.
        self.diff = OscDiff(self.bindiffdtype, scaleofstep, periodreg, True).reset(tonediffs)

    def callimpl(self):
        self.chain(self.diff)(self.blockbuf)

class NoiseDiffs(DiffRing):

    def __init__(self, nzdegrees):
        DiffRing.__init__(self, lfsr.Lfsr(nzdegrees), 0, BufNode.bindiffdtype)

class NoiseOsc(BufNode):

    def __init__(self, scale, periodreg, noisediffs):
        BufNode.__init__(self, self.binarydtype)
        scaleofstep = scale * 2 # This results in authentic spectrum, see qnoispec.
        self.diff = OscDiff(self.bindiffdtype, scaleofstep, periodreg, False).reset(noisediffs)

    def callimpl(self):
        self.chain(self.diff)(self.blockbuf)

def sinering(steps): # Like saw but unlike triangular, we use steps for a full wave.
    unit = []
    minamp = level5toamp(0)
    for i in xrange(steps):
        amp = minamp + (1 - minamp) * (math.sin(2 * math.pi * i / steps) + 1) / 2
        unit.append(round(amptolevel5(amp)))
    return DiffRing(cycle(unit), 0, BufNode.zto127diffdtype)

class EnvOsc(BufNode):

    steps = 32
    diffs0c = DiffRing(cycle(range(steps)), 0, BufNode.bindiffdtype)
    diffs08 = DiffRing(cycle(range(steps - 1, -1, -1)), 0, BufNode.bindiffdtype)
    diffs0e = DiffRing(cycle(range(steps) + range(steps - 1, -1, -1)), 0, BufNode.bindiffdtype)
    diffs0a = DiffRing(cycle(range(steps - 1, -1, -1) + range(steps)), 0, BufNode.bindiffdtype)
    diffs0f = DiffRing(itertools.chain(xrange(steps), cycle([0])), 0, BufNode.bindiffdtype, steps)
    diffs0d = DiffRing(itertools.chain(xrange(steps), cycle([steps - 1])), 0, BufNode.bindiffdtype, steps)
    diffs0b = DiffRing(itertools.chain(xrange(steps - 1, -1, -1), cycle([steps - 1])), 0, BufNode.bindiffdtype, steps)
    diffs09 = DiffRing(itertools.chain(xrange(steps - 1, -1, -1), cycle([0])), 0, BufNode.bindiffdtype, steps)
    diffs10 = sinering(steps)

    def __init__(self, scale, periodreg, shapereg):
        BufNode.__init__(self, self.zto255dtype)
        scaleofstep = scale * 32 // self.steps
        self.diff = OscDiff(self.zto127diffdtype, scaleofstep, periodreg, True)
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
