from __future__ import division
from buf import *
import scipy.signal

class Sampler:

  def __init__(self, signal, ratio, buftype = SimpleBuf):
    self.signal = signal
    self.ratio = ratio
    self.index = -1
    self.pos = 0
    self.buf = buftype()

  def load(self):
    self.pos += self.ratio
    n = -int((self.index + 1 - self.pos) // 1) # Cheaper ceil.
    if n:
      self.signal(self.buf.atleast(n), n)
      self.last = self.buf[n - 1]
      self.index += n
    return n

class LastSampler(Sampler):

  def __call__(self, buf, samplecount):
    for bufindex in xrange(samplecount):
      self.load()
      buf[bufindex] = self.last

class FirSampler(Sampler):

  def __init__(self, signal, ratio, logtablesize):
    # The kernel is symmetric so logically we only need to tabulate one side and the central value:
    self.size = (1 << logtablesize) * 2 - 1
    Sampler.__init__(self, signal, ratio, lambda: RingBuf(self.size))
    self.kernel = scipy.signal.firwin(self.size, 1 / ratio)

  def __call__(self, buf, samplecount):
    for i in xrange(samplecount):
      self.load()
      buf[i] = self.buf.convolve(self.kernel)

class MeanSampler(Sampler):

  def __call__(self, buf, samplecount):
    for bufindex in xrange(samplecount):
      n = self.load()
      if n:
        acc = 0
        for i in xrange(n):
          acc += self.buf[i]
        buf[bufindex] = acc / n
      else:
        buf[bufindex] = self.last
