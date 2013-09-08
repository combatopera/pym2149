from __future__ import division
from dac import *

class FloatFormat:

  def __init__(self, signal):
    self.signal = signal

  def __call__(self, buf, samplecount):
    self.signal(buf, samplecount)
    buf.xform(0, samplecount, 1, -Dac.halfpoweramp)
