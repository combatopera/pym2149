from __future__ import division

class Dac:

  def __init__(self, signal, volreg, maxvol, halfvol):
    self.signal = signal
    self.volreg = volreg
    self.vol = None
    self.maxvol = maxvol
    self.voldiv = maxvol - halfvol

  def __call__(self, buf, samplecount):
    self.signal(buf, samplecount)
    if self.volreg.value != self.vol:
      self.amp = 2 ** ((self.volreg.value - self.maxvol) / self.voldiv)
      self.vol = self.volreg.value
    buf.scale(0, samplecount, self.amp)
