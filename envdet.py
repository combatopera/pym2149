from __future__ import division
import math

class EnvDet:

  rc = 1e3 * 0.1e-6 # From schematic.

  def __init__(self, signal, signalfreq):
    self.mul = math.exp(-(1 / signalfreq) / self.rc)
    self.last = 0 # Logically the value one period ago.
    self.signal = signal

  def __call__(self, buf, samplecount):
    self.signal(buf, samplecount) # Temporarily abuse target buffer.
    for bufindex in xrange(samplecount):
      self.last *= self.mul # Simulate discharge over period just gone by.
      if buf[bufindex] < self.last:
        buf[bufindex] = self.last # Discharging will continue.
      else:
        self.last = buf[bufindex] # Instant charge.
