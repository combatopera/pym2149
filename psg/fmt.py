from __future__ import division
import math

class FloatFormat:

  def __init__(self, signal, maxv):
    amp = 1 / math.sqrt(2)
    self.scale = 2 * amp / maxv
    self.add = -amp
    self.signal = signal

  def __call__(self, buf, samplecount):
    self.signal(buf, samplecount)
    buf.xform(0, samplecount, self.scale, self.add)
