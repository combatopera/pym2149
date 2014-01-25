from __future__ import division
from nod import Node
import numpy as np, math

class Level(Node):

  def __init__(self, modereg, fixedreg, env, signal):
    Node.__init__(self, self.zto255dtype) # Must be suitable for use as index downstream.
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

class Dac(Node):

  def __init__(self, level, ampshare):
    Node.__init__(self, np.uint32)
    maxamp = 2 ** 31.5 / ampshare
    # Lookup of ideal amplitudes, rounded towards zero:
    self.leveltoamp = np.array([self.dtype(leveltoamp(v) * maxamp) for v in xrange(32)])
    self.level = level

  def callimpl(self):
    self.blockbuf.mapbuf(self.chain(self.level), self.leveltoamp)
