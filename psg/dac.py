from __future__ import division
from nod import Node
import numpy as np

class Dac(Node):

  headroom = int(2 ** 31 - 2 ** 30.5) # Very close to 3 dB.
  maxvol = 15
  halfvol = 13

  def __init__(self, signal, modereg, volreg, env, ampshare):
    Node.__init__(self, np.uint32)
    self.vol = None
    self.maxamp = 2 ** 31.5 / ampshare
    self.signal = signal
    self.modereg = modereg
    self.volreg = volreg
    self.env = env

  def callimpl(self):
    if self.volreg.value != self.vol:
      self.amp = int(2 ** ((self.volreg.value - self.maxvol) / (self.maxvol - self.halfvol)) * self.maxamp)
      self.vol = self.volreg.value
    self.blockbuf.copybuf(self.signal(self.block))
    self.blockbuf.scale(self.amp)
