from __future__ import division
from nod import Node
import numpy as np

class Level(Node):

  def __init__(self, modereg, fixedreg, env, signal):
    Node.__init__(self, Node.commondtype(env, signal)) # XXX: Or just env?
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
    self.blockbuf.mulbuf(self.signal(self.block))

class Dac(Node):

  dtype = np.uint32 # SoX is 32-bit signed internally, we use unsigned as it's easier.
  headroom = int(2 ** 31 - 2 ** 30.5) # Half power point, very close to 3 dB.

  def __init__(self, level, ampshare):
    Node.__init__(self, self.dtype)
    maxamp = 2 ** 31.5 / ampshare
    self.leveltoamp = np.array([self.dtype(2 ** ((v - 31) / 4) * maxamp) for v in xrange(32)])
    self.level = level

  def callimpl(self):
    self.blockbuf.mapbuf(self.level(self.block), self.leveltoamp)
