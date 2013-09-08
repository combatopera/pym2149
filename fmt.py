from __future__ import division
import math

class U8Format:

  amp = 128 / math.sqrt(2)

  def __init__(self, signal, maxv):
    self.buf = []
    self.scale = 2 / maxv
    self.signal = signal

  def __call__(self, buf, bufstart, bufstop):
    n = bufstop - bufstart
    if len(self.buf) < n:
      self.buf = [None] * n
    self.signal(self.buf, 0, n)
    for i in xrange(n):
      buf[bufstart + i] = int(128 + (self.buf[i] * self.scale - 1) * self.amp) # Effectively floor.
