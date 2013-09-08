from __future__ import division
from buf import *
import math, array

class LEFormat:

  def __init__(self, signed, bits, signal, maxv):
    self.buf = Buf()
    half = 1 << (bits - 1)
    amp = half / math.sqrt(2)
    self.scale = 2 * amp / maxv
    self.shift = half - amp
    self.octets = (bits + 7) // 8
    self.umax = (1 << bits) - 1
    self.subtract = [0, half][signed]
    self.signal = signal

  def createoutbuf(self, count):
    return array.array('B', count * self.octets * [0]) # Unsigned chars as in C.

  def __call__(self, buf, count):
    self.signal(self.buf.atleast(count), 0, count)
    for i in xrange(count):
      x = int(max(0, self.buf[i] * self.scale + self.shift)) # Effectively floor.
      x = min(self.umax, x) - self.subtract # Clamp other side and apply signedness.
      for b in xrange(self.octets):
        buf[self.octets * i + b] = x & 0xff
        x >>= 8

class U8Format(LEFormat):

  def __init__(self, signal, maxv):
    LEFormat.__init__(self, False, 8, signal, maxv)

class S16LEFormat(LEFormat):

  def __init__(self, signal, maxv):
    LEFormat.__init__(self, True, 16, signal, maxv)
