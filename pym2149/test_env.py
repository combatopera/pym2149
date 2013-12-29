#!/usr/bin/env python

import unittest
from env import Env

class TestEnv(unittest.TestCase):

  def test_works(self):
    self.assertEqual([5], Env(5))
    self.assertEqual([8], Env(5).jump(8))
    self.assertEqual([5, 8], Env(5).lin(1, 8))
    self.assertEqual([5, 6, 7, 8], Env(5).lin(3, 8))
    self.assertEqual([5, 7, 8], Env(5).lin(2, 8))
    self.assertEqual([5, 6, 7, 7, 8], Env(5).lin(4, 8))
    # Negative values:
    self.assertEqual([-5, -8], Env(-5).lin(1, -8))
    self.assertEqual([-5, -6, -7, -8], Env(-5).lin(3, -8))
    self.assertEqual([-5, -7, -8], Env(-5).lin(2, -8))
    self.assertEqual([-5, -6, -7, -7, -8], Env(-5).lin(4, -8))
    # Holds:
    self.assertEqual([5, 5, 5, 5, 6, 7, 8], Env(5).hold(3).lin(3, 8))
    self.assertEqual([5, 5, 5, 8], Env(5).hold(3).jump(8))

if __name__ == '__main__':
  unittest.main()
