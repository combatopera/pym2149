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
import lfsr, itertools, math
from nod import BufNode
from dac import leveltoamp, amptolevel
from buf import Ring

class OscNode(BufNode):

  def __init__(self, dtype, periodreg):
    BufNode.__init__(self, dtype)
    self.reset()
    self.periodreg = periodreg

  def reset(self):
    self.valueindex = 0
    self.progress = self.scaleofstep * 0xffff # Matching biggest possible 16-bit stepsize.

  def getvalue(self, n = 1):
    self.warp(n - 1)
    self.lastvalue = self.values.buf[self.valueindex]
    self.warp(1)
    return self.lastvalue

  def warp(self, n):
    self.valueindex += n
    size = self.values.buf.shape[0]
    while self.valueindex >= size:
      self.valueindex = self.values.loopstart + self.valueindex - size

  def prolog(self):
    # If progress beats the new stepsize, we terminate right away:
    cursor = min(self.block.framecount, max(0, self.stepsize - self.progress))
    cursor and self.blockbuf.fillpart(0, cursor, self.lastvalue)
    self.progress = min(self.progress + cursor, self.stepsize)
    return cursor

  def common(self, cursor):
    fullsteps = (self.block.framecount - cursor) // self.stepsize
    if self.blockbuf.putringops(self.values, self.valueindex, fullsteps) * self.stepsize < fullsteps:
      for i in xrange(self.stepsize):
        self.blockbuf.putring(cursor + i, self.stepsize, self.values, self.valueindex, fullsteps)
      self.getvalue(fullsteps)
      cursor += fullsteps * self.stepsize
    else:
      for _ in xrange(fullsteps):
        self.blockbuf.fillpart(cursor, cursor + self.stepsize, self.getvalue())
        cursor += self.stepsize
    if cursor < self.block.framecount:
      self.blockbuf.fillpart(cursor, self.block.framecount, self.getvalue())
      self.progress = self.block.framecount - cursor

loopsize = 1024

class ToneDiff(BufNode):

  diffs = Ring(BufNode.binarydtype, (1 - 2 * (i & 1) for i in xrange(loopsize)), 0)

  def __init__(self, scale, periodreg):
    BufNode.__init__(self, self.bindiffdtype)
    self.scaleofstep = scale * 2 // 2 # Normally half of 16.
    self.progress = 0
    self.periodreg = periodreg
    self.index = 0
    self.dc = 0

  def callimpl(self):
    stepsize = self.scaleofstep * self.periodreg.value
    # If progress beats the new stepsize, we step right away:
    stepindex = self.progress and max(0, stepsize - self.progress)
    if stepindex >= self.block.framecount:
      # Next step of waveform is beyond this block:
      self.progress += self.block.framecount
      return self.hold
    self.blockbuf.fill(0)
    stepcount = (self.block.framecount - stepindex + stepsize - 1) // stepsize
    self.blockbuf.putring(stepindex, stepsize, self.diffs, self.index, stepcount)
    self.blockbuf.addtofirst(self.dc) # Add last value of previous integral.
    self.progress = (self.block.framecount - stepindex) % stepsize
    # The state changes iff we did an odd number of steps just now:
    if stepcount & 1:
      self.index = 1 - self.index
      self.dc = 1 - self.dc
    return self.integral

  def hold(self, tonebuf):
    tonebuf.fill(self.dc)

  def integral(self, tonebuf):
    tonebuf.integrate(self.blockbuf)

class ToneOsc(BufNode):

  def __init__(self, scale, periodreg):
    BufNode.__init__(self, self.binarydtype)
    self.diff = ToneDiff(scale, periodreg)

  def callimpl(self):
    self.chain(self.diff)(self.blockbuf)

class NoiseOsc(OscNode):

  values = Ring(BufNode.binarydtype, lfsr.Lfsr(*lfsr.ym2149nzdegrees), 0)

  def __init__(self, scale, periodreg):
    self.scaleofstep = scale * 2 # This results in authentic spectrum, see qnoispec.
    OscNode.__init__(self, BufNode.binarydtype, periodreg)
    self.stepsize = self.progress

  def callimpl(self):
    cursor = self.prolog()
    if cursor < self.block.framecount:
      self.progress = self.stepsize = self.scaleofstep * self.periodreg.value
      self.common(cursor)

def cycle(unit): # Unlike itertools version, we assume unit can be iterated more than once.
  unitsize = len(unit)
  if 0 != loopsize % unitsize:
    raise Exception("Unit size %s does not divide %s." % (unitsize, loopsize))
  for _ in xrange(loopsize // unitsize):
    for x in unit:
      yield x

def sinering(steps): # Like saw but unlike triangular, we use steps for a full wave.
  levels = []
  minamp = leveltoamp(0)
  for i in xrange(steps):
    amp = minamp + (1 - minamp) * (math.sin(2 * math.pi * i / steps) + 1) / 2
    levels.append(round(amptolevel(amp)))
  return Ring(BufNode.zto255dtype, cycle(levels), 0)

class EnvOsc(OscNode):

  steps = 32
  values0c = Ring(BufNode.zto255dtype, cycle(range(steps)), 0)
  values08 = Ring(BufNode.zto255dtype, cycle(range(steps - 1, -1, -1)), 0)
  values0e = Ring(BufNode.zto255dtype, cycle(range(steps) + range(steps - 1, -1, -1)), 0)
  values0a = Ring(BufNode.zto255dtype, cycle(range(steps - 1, -1, -1) + range(steps)), 0)
  values0f = Ring(BufNode.zto255dtype, itertools.chain(xrange(steps), cycle([0])), steps)
  values0d = Ring(BufNode.zto255dtype, itertools.chain(xrange(steps), cycle([steps - 1])), steps)
  values0b = Ring(BufNode.zto255dtype, itertools.chain(xrange(steps - 1, -1, -1), cycle([steps - 1])), steps)
  values09 = Ring(BufNode.zto255dtype, itertools.chain(xrange(steps - 1, -1, -1), cycle([0])), steps)
  values10 = sinering(steps)

  def __init__(self, scale, periodreg, shapereg):
    self.scaleofstep = scale * 32 // self.steps
    OscNode.__init__(self, BufNode.zto255dtype, periodreg)
    self.shapeversion = None
    self.shapereg = shapereg

  def callimpl(self):
    if self.shapeversion != self.shapereg.version:
      shape = self.shapereg.value
      if shape == (shape & 0x07):
        shape = (0x09, 0x0f)[bool(shape & 0x04)]
      self.values = getattr(self, "values%02x" % shape)
      self.shapeversion = self.shapereg.version
      self.reset()
    self.stepsize = self.scaleofstep * self.periodreg.value
    cursor = self.prolog()
    if cursor < self.block.framecount:
      self.common(cursor)
