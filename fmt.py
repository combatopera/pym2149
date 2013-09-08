from __future__ import division
import math

class U8Format:

  amp = 128 / math.sqrt(2)

  def __init__(self, signal, maxv):
    self.buf = []
    self.scale = 2 * self.amp / maxv
    self.shift = 128 - self.amp
    self.signal = signal

  def __call__(self, buf, bufstart, bufstop):
    n = bufstop - bufstart
    if len(self.buf) < n:
      self.buf = [None] * n
    self.signal(self.buf, 0, n)
    for i in xrange(n):
      buf[bufstart + i] = int(max(0, self.buf[i] * self.scale + self.shift)) # Effectively floor.
