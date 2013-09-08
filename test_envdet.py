#!/usr/bin/env python

import unittest, math
from envdet import *

class TestEnvDet(unittest.TestCase):

  class Signal:

    def __init__(self, first, second):
      self.first = first
      self.second = second

    def __call__(self, buf, bufstart, bufstop):
      mid = (bufstart + bufstop) / 2
      for i in xrange(bufstart, mid):
        buf[i] = self.first
      for i in xrange(mid, bufstop):
        buf[i] = self.second

  def test_discharge(self):
    buf = [None] * 8
    EnvDet(self.Signal(3, 2.1), 1e5)(buf, 0, 8)
    self.assertEqual([3] * 4, buf[:4])
    self.assertAlmostEqual(3 * math.exp(-1e-5 / EnvDet.rc), buf[4])
    self.assertAlmostEqual(3 * math.exp(-2e-5 / EnvDet.rc), buf[5])
    self.assertAlmostEqual(3 * math.exp(-3e-5 / EnvDet.rc), buf[6])
    self.assertEqual(2.1, buf[7])

  def test_charge(self):
    buf = [None] * 8
    EnvDet(self.Signal(2.1, 3), 1e5)(buf, 0, 8)
    self.assertEqual([2.1] * 4, buf[:4])
    self.assertEqual([3] * 4, buf[4:])

if __name__ == '__main__':
  unittest.main()
