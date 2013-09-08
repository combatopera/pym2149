from __future__ import division
from buf import *
import math

class U8Format:

  amp = 128 / math.sqrt(2)

  def __init__(self, signal, maxv):
    self.buf = Buf()
    self.scale = 2 * self.amp / maxv
    self.shift = 128 - self.amp
    self.signal = signal

  def __call__(self, buf, bufstart, bufstop):
    n = bufstop - bufstart
    self.signal(self.buf.atleast(n), 0, n)
    for i in xrange(n):
      buf[bufstart + i] = int(max(0, self.buf[i] * self.scale + self.shift)) # Effectively floor.
