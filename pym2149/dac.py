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
from nod import BufNode
import numpy as np, math

class Level(BufNode):

  def to5bit(level4bit):
    return level4bit * 2 + 1 # Observe 4-bit 0 is 5-bit 1.

  pwmzero4bit = 0 # TODO: Make this a register.
  pwmzero5bit = to5bit(pwmzero4bit)
  lookup = np.fromiter([pwmzero5bit] + range(32), BufNode.zto255dtype)

  to5bit = staticmethod(to5bit)

  def __init__(self, levelmodereg, fixedreg, env, signal, rtone, timereffectreg):
    BufNode.__init__(self, self.zto255dtype) # Must be suitable for use as index downstream.
    self.levelmodereg = levelmodereg
    self.fixedreg = fixedreg
    self.env = env
    self.signal = signal
    self.rtone = rtone
    self.timereffectreg = timereffectreg

  def callimpl(self):
    timereffect = self.timereffectreg.value
    if timereffect is not None:
      timereffect(self)
    elif self.levelmodereg.value:
      self.blockbuf.copybuf(self.chain(self.signal))
      self.blockbuf.mulbuf(self.chain(self.env))
    else:
      self.blockbuf.copybuf(self.chain(self.signal))
      self.blockbuf.mul(self.to5bit(self.fixedreg.value))

def pwmeffect(levelnode):
    if levelnode.levelmodereg.value:
        # TODO: Test this branch.
        levelnode.blockbuf.copybuf(levelnode.chain(levelnode.env)) # Values in [0, 31].
        levelnode.blockbuf.add(1) # Shift env values to [1, 32].
        levelnode.blockbuf.mulbuf(levelnode.chain(levelnode.signal)) # Introduce 0.
        levelnode.blockbuf.mulbuf(levelnode.chain(levelnode.rtone)) # Introduce more 0.
        levelnode.blockbuf.mapbuf(levelnode.blockbuf, levelnode.lookup) # Map 0 to 5-bit pwmzero and sub 1 from rest.
    else:
        levelnode.blockbuf.copybuf(levelnode.chain(levelnode.signal))
        levelnode.blockbuf.mulbuf(levelnode.chain(levelnode.rtone))
        # Map 0 to pwmzero and 1 to fixed level:
        levelnode.blockbuf.mul(levelnode.to5bit(levelnode.fixedreg.value) - levelnode.pwmzero5bit)
        levelnode.blockbuf.add(levelnode.pwmzero5bit)

log2 = math.log(2)

def leveltoamp(level):
  return 2 ** ((level - 31) / 4)

def amptolevel(amp):
  return 31 + 4 * math.log(amp) / log2

class Dac(BufNode):

  def __init__(self, level, log2maxpeaktopeak, ampshare):
    BufNode.__init__(self, self.floatdtype)
    # We take off .5 so that the peak amplitude is about -3 dB:
    maxpeaktopeak = (2 ** (log2maxpeaktopeak - .5)) / ampshare
    # Lookup of ideal amplitudes:
    self.leveltopeaktopeak = np.fromiter((leveltoamp(v) * maxpeaktopeak for v in xrange(32)), self.dtype)
    self.level = level

  def callimpl(self):
    self.blockbuf.mapbuf(self.chain(self.level), self.leveltopeaktopeak)
