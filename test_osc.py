#!/usr/bin/env python

import unittest, lfsr
from osc import *

class Reg:

  def __init__(self, value):
    self.value = value

class TestToneOsc(unittest.TestCase):

  def test_works(self):
    v = [None] * 96
    ToneOsc(Reg(3))(v, 0, 96)
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:48])
    self.assertEqual([1] * 24, v[48:72])
    self.assertEqual([0] * 24, v[72:])

class TestNoiseOsc(unittest.TestCase):

  def test_works(self):
    n = 100
    v = [None] * (48 * n)
    NoiseOsc(Reg(3))(v, 0, len(v))
    u = lfsr.Lfsr(*lfsr.ym2149nzdegrees)
    for i in xrange(n):
      self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

if __name__ == '__main__':
  unittest.main()
