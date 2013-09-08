#!/usr/bin/env python

import unittest
from sampler import *

class Counter:

  def __init__(self):
    self.x = 0

  def __call__(self, buf, samplecount):
    for bufindex in xrange(samplecount):
      buf[bufindex] = self.x
      self.x += 1

class TestLastSampler(unittest.TestCase):

  def test_works(self):
    buf = [None] * 10
    LastSampler(Counter(), 1)(buf, 10)
    self.assertEqual(range(10), buf)
    LastSampler(Counter(), 2)(buf, 5)
    self.assertEqual([1, 3, 5, 7, 9], buf[:5])
    LastSampler(Counter(), 1.5)(buf, 5)
    self.assertEqual([1, 2, 4, 5, 7], buf[:5])
    LastSampler(Counter(), .5)(buf, 5)
    self.assertEqual([0, 0, 1, 1, 2], buf[:5])

class TestFirSampler(unittest.TestCase):

  def test_works(self):
    buf = [None] * 10
    # Trivially-sized FirSampler behaves same as LastSampler:
    FirSampler(Counter(), 1, 0)(buf, 10)
    self.assertEqual(range(10), buf)
    FirSampler(Counter(), 2, 0)(buf, 5)
    self.assertEqual([1, 3, 5, 7, 9], buf[:5])
    FirSampler(Counter(), 1.5, 0)(buf, 5)
    self.assertEqual([1, 2, 4, 5, 7], buf[:5])
    FirSampler(Counter(), .5, 0)(buf, 5)
    self.assertEqual([0, 0, 1, 1, 2], buf[:5])

class TestMeanSampler(unittest.TestCase):

  def test_works(self):
    buf = [None] * 10
    MeanSampler(Counter(), 1)(buf, 10)
    self.assertEqual(range(10), buf)
    MeanSampler(Counter(), 2)(buf, 5)
    self.assertEqual([.5, 2.5, 4.5, 6.5, 8.5], buf[:5])
    MeanSampler(Counter(), 1.5)(buf, 5)
    self.assertEqual([.5, 2, 3.5, 5, 6.5], buf[:5])
    MeanSampler(Counter(), .5)(buf, 5)
    self.assertEqual([0, 0, 1, 1, 2], buf[:5])

if __name__ == '__main__':
  unittest.main()
