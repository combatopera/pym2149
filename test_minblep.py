#!/usr/bin/env python

import unittest, numpy as np
from minblep import MinBleps

class TestMinBleps(unittest.TestCase):

  def test_minphasereconstruction(self):
    minbleps = MinBleps(MinBleps.order(), 500)
    absdft = np.abs(np.fft.fft(minbleps.bli))
    absdft2 = np.abs(np.fft.fft(minbleps.minbli))
    self.assertTrue(np.allclose(absdft, absdft2))

if __name__ == '__main__':
  unittest.main()
