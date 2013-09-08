#!/usr/bin/env python

import unittest
from fmt import *

class Ramps:

  def __call__(self, buf, samplecount):
    for i in xrange(samplecount):
      buf[i] = i

class TestU8Format(unittest.TestCase):

  def test_works(self):
    f = U8Format(Ramps(), 10)
    v = [None] * (11 + 1)
    f(v, 11)
    self.assertEqual([37, 55, 73, 91, 109, 128, 146, 164, 182, 200, 218], v[:11])
    self.assertEqual([None], v[11:])

class TestS16LEFormat(unittest.TestCase):

  def test_works(self):
    f = S16LEFormat(Ramps(), 4)
    v = [None] * (5 * 2 + 1)
    f(v, 5) # 5 samples, each using 2 cells.
    self.assertEqual([125, 165, 190, 210, 0, 0, 65, 45, 130, 90], v[:10])
    self.assertEqual([None], v[10:])

if __name__ == '__main__':
  unittest.main()
