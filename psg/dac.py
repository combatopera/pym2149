from __future__ import division

class Dac:

  halfpoweramp = 2 ** -.5 # Very close to -3 dB.

  def __init__(self, signal, volreg, maxvol, halfvol, ampshare):
    self.signal = signal
    self.volreg = volreg
    self.vol = None
    self.maxvol = maxvol
    self.halfvol = halfvol
    self.maxamp = self.halfpoweramp * 2 / ampshare

  def __call__(self, buf):
    self.signal(buf)
    if self.volreg.value != self.vol:
      self.amp = 2 ** ((self.volreg.value - self.maxvol) / (self.maxvol - self.halfvol)) * self.maxamp
      self.vol = self.volreg.value
    buf.scale(self.amp)
