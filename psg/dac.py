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
      # Convert to equivalent 5-bit level:
      level = self.fixedreg.value * 2 + 1 # That's right, 4-bit 0 is 5-bit 1.
      self.blockbuf.fill(0, self.block.framecount, level)
    self.blockbuf.mulbuf(self.signal(self.block))

class Dac(Node):

  dtype = np.uint32
  headroom = int(2 ** 31 - 2 ** 30.5) # Very close to 3 dB.

  def __init__(self, level, ampshare):
    Node.__init__(self, self.dtype)
    maxamp = 2 ** 31.5 / ampshare
    self.leveltoamp = np.array([self.dtype(2 ** ((v - 31) / 4) * maxamp) for v in xrange(32)])
    self.level = level

  def callimpl(self):
    self.blockbuf.mapbuf(self.level(self.block), self.leveltoamp)
