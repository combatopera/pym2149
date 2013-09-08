#!/usr/bin/env python

import unittest, lfsr

class TestLfsr(unittest.TestCase):

  def test_correctsequence(self):
    expected = (0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0)
    actual = tuple(lfsr.Lfsr(17, 14))
    self.assertTrue(''.join(map(str, expected)) in ''.join(map(str, actual)))

if __name__ == '__main__':
  unittest.main()
