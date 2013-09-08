from __future__ import division
from nod import Node
import numpy as np

class Dac(Node):

  halfpoweramp = 2 ** -.5 # Very close to -3 dB.

  def __init__(self, signal, volreg, maxvol, halfvol, ampshare):
    Node.__init__(self, np.float32)
    self.vol = None
    self.maxamp = self.halfpoweramp * 2 / ampshare
    self.signal = signal
    self.volreg = volreg
    self.maxvol = maxvol
    self.halfvol = halfvol

  def callimpl(self):
    if self.volreg.value != self.vol:
      self.amp = 2 ** ((self.volreg.value - self.maxvol) / (self.maxvol - self.halfvol)) * self.maxamp
      self.vol = self.volreg.value
    self.blockbuf.copybuf(self.signal(self.block))
    self.blockbuf.scale(self.amp)
