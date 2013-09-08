#!/usr/bin/env python

import unittest
from lfsr import *

class TestLfsr(unittest.TestCase):

  def test_correctsequence(self):
    # Subsequence of the real LFSR from Hatari mailing list:
    expected = (0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0)
    actual = tuple(Lfsr(*ym2149nzdegrees))
    self.assertTrue(''.join(map(str, expected)) in ''.join(map(str, actual)))

if __name__ == '__main__':
  unittest.main()
