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

  def __init__(self, modereg, fixedreg, env, signal):
    BufNode.__init__(self, self.zto255dtype) # Must be suitable for use as index downstream.
    self.modereg = modereg
    self.fixedreg = fixedreg
    self.env = env
    self.signal = signal

  def callimpl(self):
    if self.modereg.value:
      self.blockbuf.copybuf(self.chain(self.env))
    else:
      # Convert to equivalent 5-bit level, observe 4-bit 0 is 5-bit 1:
      self.blockbuf.fill(self.fixedreg.value * 2 + 1)
    self.blockbuf.mulbuf(self.chain(self.signal))

log2 = math.log(2)

def leveltoamp(level):
  return 2 ** ((level - 31) / 4)

def amptolevel(amp):
  return 31 + 4 * math.log(amp) / log2

class Dac(BufNode):

  def __init__(self, level, ampshare):
    BufNode.__init__(self, self.floatdtype)
    maxpeaktopeak = 2 ** 15.5 / ampshare
    # Lookup of ideal amplitudes:
    self.leveltopeaktopeak = np.fromiter((leveltoamp(v) * maxpeaktopeak for v in xrange(32)), self.dtype)
    self.level = level

  def callimpl(self):
    self.blockbuf.mapbuf(self.chain(self.level), self.leveltopeaktopeak)
