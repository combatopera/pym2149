from __future__ import division

class Sampler:

  def __init__(self, signal, ratio):
    self.signal = signal
    self.ratio = ratio
    self.index = -1
    self.pos = 0

class LastSampler(Sampler):

  def __call__(self):
    self.pos += self.ratio
    while self.index < self.pos - 1:
      self.last = self.signal()
      self.index += 1
    return self.last

class MeanSampler(Sampler):

  def __call__(self):
    acc = n = 0
    self.pos += self.ratio
    while self.index < self.pos - 1:
      self.last = self.signal()
      self.index += 1
      acc += self.last
      n += 1
    if not n:
      return self.last
    return acc / n
