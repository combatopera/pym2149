from __future__ import division

class Sampler:

  def __init__(self, signal, ratio):
    self.signal = signal
    self.ratio = ratio
    self.index = -1
    self.pos = 0

class LastSampler(Sampler):

  def __call__(self, buf, bufstart, bufstop):
    v = [None]
    for bufindex in xrange(bufstart, bufstop):
      self.pos += self.ratio
      while self.index < self.pos - 1:
        self.signal(v, 0, 1)
        self.last = v[0]
        self.index += 1
      buf[bufindex] = self.last

class MeanSampler(Sampler):

  def __call__(self, buf, bufstart, bufstop):
    v = [None]
    for bufindex in xrange(bufstart, bufstop):
      acc = n = 0
      self.pos += self.ratio
      while self.index < self.pos - 1:
        self.signal(v, 0, 1)
        self.last = v[0]
        self.index += 1
        acc += self.last
        n += 1
      if n:
        buf[bufindex] = acc / n
      else:
        buf[bufindex] = self.last
