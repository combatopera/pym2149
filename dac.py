from __future__ import division

class Dac:

  def __init__(self, signal, volreg, maxvol, halfvol):
    self.signal = signal
    self.volreg = volreg
    self.getamp = lambda: 2 ** ((volreg.value - maxvol) / (maxvol - halfvol))

  def __call__(self, buf, samplecount):
    self.signal(buf, samplecount)
    amp = self.getamp()
    for bufindex in xrange(samplecount):
      buf[bufindex] *= amp
