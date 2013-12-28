#!/usr/bin/env python

import unittest
from env import Env

class TestEnv(unittest.TestCase):

  def test_works(self):
    e = Env(5).lineto(1, 1, 9).lineto(2, -2, 4)
    for i, x in enumerate([5, 6, 7, 8, 9, 9, 7, 7, 5, 5, 4, 4, 4]):
      self.assertEqual(x, e(i))
    e = Env(4).lineto(2, -3, -5).lineto(1, 1, -3)
    for i, x in enumerate([4, 4, 1, 1, -2, -2, -5, -4, -3, -3]):
      self.assertEqual(x, e(i))
    e = Env(10).lineto(66, 99, 10).lineto(1, 1, 11)
    for i, x in enumerate([10, 11, 11]):
      self.assertEqual(x, e(i))

if __name__ == '__main__':
  unittest.main()
