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
import lfsr, itertools, math, numpy as np, fractions
from nod import BufNode
from dac import leveltoamp, amptolevel
from buf import DiffRing, RingCursor
from fractions import Fraction

mfpclock = 2457600
loopsize = 1024

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

def fracceil(f):
  return -((-f.numerator) // f.denominator)

def fracfloor(f):
  return f.numerator // f.denominator

def fraclcd(f, g): # The LCD is the LCM of the denominators.
  fd = f.denominator
  gd = g.denominator
  return fd * gd // fractions.gcd(fd, gd)

def fracint(f, denominator):
  com = fractions.gcd(f.denominator, denominator) # To prevent overflow, not as slow as it looks.
  return f.numerator * (denominator//com) // (f.denominator//com)

def fracfloor2(f, g):
  com = fractions.gcd(f.denominator, g.denominator)
  return f.numerator * (g.denominator//com) // ((f.denominator//com) * g.numerator)

def fracsub(f, g):
  com = fractions.gcd(f.denominator, g.denominator)
  fd = f.denominator // com
  gd = g.denominator // com
  return Fraction(f.numerator * gd - g.numerator * fd, fd * gd * com)

class RationalDiff(BinDiff):

  def __init__(self, dtype, chipimplclock, periodreg):
    BinDiff.__init__(self, dtype)
    self.chipimplclock = chipimplclock
    self.periodreg = periodreg

  def callimpl(self):
    if not self.periodreg.value:
      # Halt interrupts. XXX: Is this authentic?
      if not self.progress:
        self.blockbuf.fill(0)
        dc = self.ringcursor.currentdc()
        self.ringcursor.put2(self.blockbuf, np.zeros(1, dtype = np.int32))
        self.blockbuf.addtofirst(dc)
        self.progress = self.block.framecount
        return self.integral
      else:
        self.progress += self.block.framecount
        return self.hold
    stepsize = Fraction(self.periodreg.value * self.chipimplclock, 2)
    if 0 == self.progress:
      stepindex = 0
    else:
      stepindex = fracsub(stepsize, self.progress)
      if fracceil(stepindex) < 0:
        stepindex = 0
    if fracceil(stepindex) >= self.block.framecount:
      self.progress += self.block.framecount
      return self.hold
    else:
      self.blockbuf.fill(0)
      stepcount = fracfloor2(self.block.framecount - 1 - stepindex, stepsize) + 1
      lcd = fraclcd(stepsize, stepindex)
      indices = -((-fracint(stepindex, lcd) - np.arange(stepcount) * fracint(stepsize, lcd)) // lcd)
      dc = self.ringcursor.currentdc()
      # Note values can integrate to 2 if there was an overflow earlier.
      self.ringcursor.put2(self.blockbuf, indices)
      self.blockbuf.addtofirst(dc)
      self.progress = fracsub(self.block.framecount - (stepcount - 1) * stepsize, stepindex)
      if self.progress == stepsize:
        self.progress = 0
      return self.integral

class RToneOsc(BufNode):

  def __init__(self, chipimplclock, periodreg):
    BufNode.__init__(self, self.binarydtype)
    self.diff = RationalDiff(self.bindiffdtype, chipimplclock, periodreg).reset(ToneOsc.diffs)

  def callimpl(self):
    self.chain(self.diff)(self.blockbuf)

class ToneOsc(BufNode):

  diffs = DiffRing((1 - (i & 1) for i in xrange(loopsize)), 0, BufNode.bindiffdtype)

  def __init__(self, scale, periodreg):
    BufNode.__init__(self, self.binarydtype)
    scaleofstep = scale * 2 // 2 # Normally half of 16.
    self.diff = OscDiff(self.bindiffdtype, scaleofstep, periodreg, True).reset(self.diffs)

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

def cycle(unit): # Unlike itertools version, we assume unit can be iterated more than once.
  unitsize = len(unit)
  if 0 != loopsize % unitsize:
    raise Exception("Unit size %s does not divide %s." % (unitsize, loopsize))
  for _ in xrange(loopsize // unitsize):
    for x in unit:
      yield x

def sinering(steps): # Like saw but unlike triangular, we use steps for a full wave.
  unit = []
  minamp = leveltoamp(0)
  for i in xrange(steps):
    amp = minamp + (1 - minamp) * (math.sin(2 * math.pi * i / steps) + 1) / 2
    unit.append(round(amptolevel(amp)))
  return DiffRing(cycle(unit), 0, BufNode.bindiffdtype)

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
