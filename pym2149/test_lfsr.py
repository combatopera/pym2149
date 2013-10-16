#!/usr/bin/env python

import unittest
from lfsr import Lfsr, ym2149nzdegrees

class TestLfsr(unittest.TestCase):

  def test_correctsequence(self):
    # Subsequence of the real LFSR from Hatari mailing list:
    expected = (0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0)
    # According to qnoispec, raw LFSR 1 maps to amp 0, so we flip our LFSR:
    expected = [1 - x for x in expected]
    actual = tuple(Lfsr(*ym2149nzdegrees))
    self.assertTrue(''.join(map(str, expected)) in ''.join(map(str, actual)))

if __name__ == '__main__':
  unittest.main()
