from __future__ import division
from buf import *
import math

class Sampler:

  def __init__(self, signal, ratio):
    self.signal = signal
    self.ratio = ratio
    self.index = -1
    self.pos = 0
    self.buf = Buf()

  def load(self):
    self.pos += self.ratio
    n = int(math.ceil(self.pos - 1 - self.index))
    if n:
      self.signal(self.buf.atleast(n), 0, n)
      self.last = self.buf[n - 1]
      self.index += n
    return n

class LastSampler(Sampler):

  def __call__(self, buf, bufstart, bufstop):
    for bufindex in xrange(bufstart, bufstop):
      self.load()
      buf[bufindex] = self.last

class MeanSampler(Sampler):

  def __call__(self, buf, bufstart, bufstop):
    for bufindex in xrange(bufstart, bufstop):
      n = self.load()
      if n:
        acc = 0
        for i in xrange(n):
          acc += self.buf[i]
        buf[bufindex] = acc / n
      else:
        buf[bufindex] = self.last
