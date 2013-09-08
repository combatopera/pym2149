from __future__ import division
import math

class EnvDet:

  rc = 1e3 * 0.1e-6 # From schematic.

  def __init__(self, signal, f):
    period = 1 / f
    self.mul = math.exp(-period / self.rc)
    self.v = 0 # Logically the value one period ago.
    self.signal = signal

  def __call__(self, buf, bufstart, bufstop):
    self.signal(buf, bufstart, bufstop)
    for bufindex in xrange(bufstart, bufstop):
      buf[bufindex] = self.v = max(buf[bufindex], self.mul * self.v)
