from __future__ import division
import math

class EnvDet:

  rc = 1e3 * 0.1e-6 # From schematic.

  def __init__(self, signal, signalfreq):
    self.mul = math.exp(-(1 / signalfreq) / self.rc)
    self.last = 0 # Logically the value one period ago.
    self.signal = signal

  def __call__(self, buf, bufstart, bufstop):
    self.signal(buf, bufstart, bufstop) # Temporarily abuse target buffer.
    for bufindex in xrange(bufstart, bufstop):
      self.last *= self.mul
      if self.last > buf[bufindex]:
        buf[bufindex] = self.last
      else:
        self.last = buf[bufindex]
