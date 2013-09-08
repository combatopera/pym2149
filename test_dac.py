#!/usr/bin/env python

import unittest
from dac import *

class Ramps:

  def __call__(self, buf, samplecount):
    for i in xrange(samplecount):
      buf[i] = i

class TestDac(unittest.TestCase):

  def test_works(self):
    v = [None] * 4
    d = Dac(Ramps(), self, 15, 13)
    self.value = 15
    d(v, 3)
    self.assertEqual([0, 1, 2, None], v)
    self.value = 13
    d(v, 3)
    self.assertEqual([0, .5, 1, None], v)
    d = Dac(Ramps(), self, 31, 27)
    self.value = 31
    d(v, 3)
    self.assertEqual([0, 1, 2, None], v)
    self.value = 23
    d(v, 3)
    self.assertEqual([0, .25, .5, None], v)

if __name__ == '__main__':
  unittest.main()
