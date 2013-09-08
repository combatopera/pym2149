from __future__ import division
from nod import Node
import numpy as np

class Level(Node):

  def __init__(self, modereg, fixedreg, env, signal):
    # Probably not necessary for dtype of signal to match that of env and this:
    Node.__init__(self, Node.commondtype(env, signal))
    self.modereg = modereg
    self.fixedreg = fixedreg
    self.env = env
    self.signal = signal

  def callimpl(self):
    if self.modereg.value:
      self.blockbuf.copybuf(self.env(self.block))
    else:
      # Convert to equivalent 5-bit level, observe 4-bit 0 is 5-bit 1:
      self.blockbuf.fill(self.fixedreg.value * 2 + 1)
    # TODO: Find out whether tone+noise should result in mostly envelope or mostly zero:
    self.blockbuf.mulbuf(self.signal(self.block))

class Dac(Node):

  datum = int(2 ** 30.5) # Half power point, very close to -3 dB.

  def __init__(self, level, ampshare):
    # The level dtype must be such that its values can be used as indices.
    dtype = np.int32 # Same as SoX internal sample format.
    Node.__init__(self, dtype)
    maxamp = 2 ** 31.5 / ampshare
    # Lookup of ideal amplitudes, rounded towards zero:
    self.leveltoamp = np.array([dtype(2 ** ((v - 31) / 4) * maxamp) for v in xrange(32)])
    self.level = level

  def callimpl(self):
    self.blockbuf.mapbuf(self.level(self.block), self.leveltoamp)
