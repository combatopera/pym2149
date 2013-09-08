from __future__ import division
from buf import *
import math

class Format:

  def __init__(self, bits, signal, maxv):
    self.buf = Buf()
    amp = (1 << (bits - 1)) / math.sqrt(2)
    self.scale = 2 * amp / maxv
    self.shift = (1 << (bits - 1)) - amp
    self.signal = signal

class U8Format(Format):

  def __init__(self, signal, maxv):
    Format.__init__(self, 8, signal, maxv)

  def __call__(self, buf, bufstart, bufstop):
    n = bufstop - bufstart
    self.signal(self.buf.atleast(n), 0, n)
    for i in xrange(n):
      buf[bufstart + i] = int(max(0, self.buf[i] * self.scale + self.shift)) # Effectively floor.

class S16LEFormat(Format):

  def __init__(self, signal, maxv):
    Format.__init__(self, 16, signal, maxv)

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
