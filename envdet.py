from __future__ import division
import math

class EnvDet:

  rc = 0.1e-6 * 1e3 # From schematic.

  def __init__(self, f):
    period = 1 / f
    self.mul = math.exp(-period / self.rc)
    self.v = 0 # Logically the value one period ago.

  def __call__(self, v):
    self.v = max(v, self.mul * self.v)
    return self.v
