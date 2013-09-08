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

class S16LEFormat:

  amp = 32768 / math.sqrt(2)

  def __init__(self, signal, maxv):
    self.buf = Buf()
    self.scale = 2 * self.amp / maxv
    self.shift = 32768 - self.amp
    self.signal = signal

  def __call__(self, buf, bufstart, bufstop):
    n = (bufstop - bufstart) / 2
    if n != int(n):
      raise Exception
    n = int(n)
    self.signal(self.buf.atleast(n), 0, n)
    for i in xrange(n):
      x = min(32767, (int(max(0, self.buf[i] * self.scale + self.shift)) - 32768))
      buf[bufstart + 2 * i] = x & 0xff
      x >>= 8
      buf[bufstart + 2 * i + 1] = x & 0xff
