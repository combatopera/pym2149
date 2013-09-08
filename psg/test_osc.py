#!/usr/bin/env python

import unittest, lfsr
from osc import ToneOsc, NoiseOsc
from nod import Block
from reg import Register

class TestToneOsc(unittest.TestCase):

  def test_works(self):
    o = ToneOsc(Register(3))
    v = o(Block(96)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:48])
    self.assertEqual([1] * 24, v[48:72])
    self.assertEqual([0] * 24, v[72:])
    v = o(Block(48)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:])

  def test_resume(self):
    o = ToneOsc(Register(3))
    v = o(Block(25)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0], v[24:])
    v = o(Block(24)).tolist()
    self.assertEqual([0] * 23, v[:23])
    self.assertEqual([1], v[23:])

class TestNoiseOsc(unittest.TestCase):

  def test_works(self):
    n = 100
    o = NoiseOsc(Register(3))
    u = lfsr.Lfsr(*lfsr.ym2149nzdegrees)
    for _ in xrange(2):
      v = o(Block(48 * n)).tolist()
      for i in xrange(n):
        self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

if __name__ == '__main__':
  unittest.main()
