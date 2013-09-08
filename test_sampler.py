#!/usr/bin/env python

import unittest
from sampler import *

class TestSampler(unittest.TestCase):

  class Counter:

    def __init__(self):
      self.x = 0

    def __call__(self):
      self.x += 1
      return self.x - 1

  def test_works(self):
    s = Sampler(self.Counter(), 1)
    self.assertEqual(range(10), [s() for i in xrange(10)])
    s = Sampler(self.Counter(), 2)
    self.assertEqual([0, 2, 4, 6, 8], [s() for i in xrange(5)])
    s = Sampler(self.Counter(), 1.5)
    self.assertEqual([0, 1.5, 3, 4.5, 6], [s() for i in xrange(5)])
    s = Sampler(self.Counter(), .5)
    self.assertEqual([0, .5, 1, 1.5, 2], [s() for i in xrange(5)])

if __name__ == '__main__':
  unittest.main()
