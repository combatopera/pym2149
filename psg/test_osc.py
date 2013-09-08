#!/usr/bin/env python

import unittest, lfsr
from osc import ToneOsc, NoiseOsc
from nod import Block

class Reg:

  def __init__(self, value):
    self.value = value

class TestToneOsc(unittest.TestCase):

  def test_works(self):
    v = ToneOsc(Reg(3))(Block(96)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:48])
    self.assertEqual([1] * 24, v[48:72])
    self.assertEqual([0] * 24, v[72:])

  def test_stopping(self):
    v = ToneOsc(Reg(3))(Block(25)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0], v[24:])

class TestNoiseOsc(unittest.TestCase):

  def test_works(self):
    n = 100
    v = NoiseOsc(Reg(3))(Block(48 * n)).tolist()
    u = lfsr.Lfsr(*lfsr.ym2149nzdegrees)
    for i in xrange(n):
      self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

if __name__ == '__main__':
  unittest.main()
