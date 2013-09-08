from __future__ import division
from buf import *
import math, array

class Format:

  def __init__(self, bits, signal, maxv):
    self.buf = Buf()
    amp = (1 << (bits - 1)) / math.sqrt(2)
    self.scale = 2 * amp / maxv
    self.shift = (1 << (bits - 1)) - amp
    self.octets = (bits + 7) // 8
    self.signal = signal

  def createoutbuf(self, count):
    return array.array('B', count * self.octets * [0]) # Unsigned chars as in C.

class U8Format(Format):

  def __init__(self, signal, maxv):
    Format.__init__(self, 8, signal, maxv)

  def __call__(self, buf, count):
    self.signal(self.buf.atleast(count), 0, count)
    for i in xrange(count):
      buf[i] = int(max(0, self.buf[i] * self.scale + self.shift)) # Effectively floor.

class S16LEFormat(Format):

  def __init__(self, signal, maxv):
    Format.__init__(self, 16, signal, maxv)

  def __call__(self, buf, count):
    self.signal(self.buf.atleast(count), 0, count)
    for i in xrange(count):
      x = min(32767, (int(max(0, self.buf[i] * self.scale + self.shift)) - 32768))
      buf[2 * i] = x & 0xff
      x >>= 8
      buf[2 * i + 1] = x & 0xff
