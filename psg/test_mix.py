#!/usr/bin/env python

import unittest
from mix import *
from buf import *

class Counter:

  def __init__(self):
    self.x = 0

  def __call__(self, buf, samplecount):
    for bufindex in xrange(samplecount):
      buf[bufindex] = self.x
      self.x += 1

class TestMixer(unittest.TestCase):

  def test_works(self):
    c = Counter()
    c(SimpleBuf().atleast(10), 10)
    d = Counter()
    m = Mixer(c, d)
    buf = SimpleBuf()
    m(buf.atleast(5), 5)
    self.assertEqual([10, 12, 14, 16, 18], list(buf[:5]))
    # Check the buffer is actually cleared first:
    m(buf, 5)
    self.assertEqual([20, 22, 24, 26, 28], list(buf[:5]))

if __name__ == '__main__':
  unittest.main()
