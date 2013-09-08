#!/usr/bin/env python

import unittest
from sampler import *

class Counter:

  def __init__(self):
    self.x = 0

  def __call__(self):
    self.x += 1
    return self.x - 1

class TestLastSampler(unittest.TestCase):

  def test_works(self):
    s = LastSampler(Counter(), 1)
    self.assertEqual(range(10), [s() for i in xrange(10)])
    s = LastSampler(Counter(), 2)
    self.assertEqual([1, 3, 5, 7, 9], [s() for i in xrange(5)])
    s = LastSampler(Counter(), 1.5)
    self.assertEqual([1, 2, 4, 5, 7], [s() for i in xrange(5)])
    s = LastSampler(Counter(), .5)
    self.assertEqual([0, 0, 1, 1, 2], [s() for i in xrange(5)])

class TestMeanSampler(unittest.TestCase):

  def test_works(self):
    s = MeanSampler(Counter(), 1)
    self.assertEqual(range(10), [s() for i in xrange(10)])
    s = MeanSampler(Counter(), 2)
    self.assertEqual([.5, 2.5, 4.5, 6.5, 8.5], [s() for i in xrange(5)])
    s = MeanSampler(Counter(), 1.5)
    self.assertEqual([.5, 2, 3.5, 5, 6.5], [s() for i in xrange(5)])
    s = MeanSampler(Counter(), .5)
    self.assertEqual([0, 0, 1, 1, 2], [s() for i in xrange(5)])

if __name__ == '__main__':
  unittest.main()
