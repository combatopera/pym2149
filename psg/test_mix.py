#!/usr/bin/env python

import unittest
from mix import *
from buf import *
from dac import *

class Counter:

  def __init__(self):
    self.x = 0

  def __call__(self, buf):
    for frameindex in xrange(buf.framecount()):
      buf[frameindex] = self.x
      self.x += 1

def expect(*values):
  return [v - Dac.halfpoweramp for v in values]

class TestMixer(unittest.TestCase):

  def test_works(self):
    c = Counter()
    c(MasterBuf(10))
    d = Counter()
    m = Mixer(c, d)
    buf = MasterBuf(5)
    m(buf)
    self.assertEqual(expect(10, 12, 14, 16, 18), list(buf[:5]))
    # Check the buffer is actually cleared first:
    m(buf)
    self.assertEqual(expect(20, 22, 24, 26, 28), list(buf[:5]))

if __name__ == '__main__':
  unittest.main()
