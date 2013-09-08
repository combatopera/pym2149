from __future__ import division

class FloatFormat:

  def __init__(self, signal, maxv):
    amp = 2 ** -.5 # Half power amplitude, very close to -3 dB.
    self.scale = 2 * amp / maxv
    self.add = -amp
    self.signal = signal

  def __call__(self, buf, samplecount):
    self.signal(buf, samplecount)
    buf.xform(0, samplecount, self.scale, self.add)
