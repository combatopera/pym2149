from __future__ import division
from nod import Node
import numpy as np

class Dac(Node):

  headroom = int(2 ** 31 - 2 ** 30.5) # Very close to 3 dB.

  def __init__(self, signal, modereg, volreg, env, ampshare):
    Node.__init__(self, np.uint32)
    maxamp = 2 ** 31.5 / ampshare
    def createlookup(maxvol, halfvol):
      return dict([v, int(2 ** ((v - maxvol) / (maxvol - halfvol)) * maxamp)] for v in xrange(maxvol + 1))
    self.fixedamps = createlookup(15, 13)
    varamps = createlookup(31, 27)
    self.varamps = np.frompyfunc(lambda x: varamps[x], 1, 1)
    self.signal = signal
    self.modereg = modereg
    self.volreg = volreg
    self.env = env

  def callimpl(self):
    self.blockbuf.copybuf(self.signal(self.block))
    if self.modereg.value:
      self.blockbuf.mulbuf(self.env(self.block))
      self.blockbuf.transform(self.varamps)
    else:
      self.blockbuf.scale(self.fixedamps[self.volreg.value])
