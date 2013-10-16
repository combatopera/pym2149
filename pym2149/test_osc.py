#!/usr/bin/env python

from __future__ import division
import unittest, lfsr, time
from osc import ToneOsc, NoiseOsc, EnvOsc
from nod import Block
from reg import Reg

class TestToneOsc(unittest.TestCase):

  def test_works(self):
    o = ToneOsc(Reg(3))
    v = o(Block(96)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:48])
    self.assertEqual([1] * 24, v[48:72])
    self.assertEqual([0] * 24, v[72:])
    v = o(Block(48)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:])

  def test_resume(self):
    o = ToneOsc(Reg(3))
    v = o(Block(25)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0], v[24:])
    v = o(Block(24)).tolist()
    self.assertEqual([0] * 23, v[:23])
    self.assertEqual([1], v[23:])

class TestNoiseOsc(unittest.TestCase):

  def test_works(self):
    n = 100
    o = NoiseOsc(Reg(3))
    u = lfsr.Lfsr(*lfsr.ym2149nzdegrees)
    for _ in xrange(2):
      v = o(Block(48 * n)).tolist()
      for i in xrange(n):
        self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

  def test_performance(self):
    blockrate = 50
    blocksize = 2000000 // blockrate
    for p in 0x01, 0x1f:
      r = Reg(p)
      o = NoiseOsc(r)
      start = time.time()
      for _ in xrange(blockrate):
        o(Block(blocksize))
      self.assertTrue(time.time() - start < .05)

class TestEnvOsc(unittest.TestCase):

  def test_08(self):
    shapereg = Reg(0x08)
    periodreg = Reg(3)
    o = EnvOsc(periodreg, shapereg)
    for _ in xrange(2):
      v = o(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

  def test_09(self):
    for shape in xrange(0x04):
      o = EnvOsc(Reg(3), Reg(shape))
      v = o(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
      self.assertEqual([0] * (8 * 3 * 34), o(Block(8 * 3 * 34)).tolist())

  def test_0a(self):
    shapereg = Reg(0x0a)
    periodreg = Reg(3)
    o = EnvOsc(periodreg, shapereg)
    v = o(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
    v = o(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
    v = o(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

  def test_0c(self):
    shapereg = Reg(0x0c)
    periodreg = Reg(3)
    o = EnvOsc(periodreg, shapereg)
    for _ in xrange(2):
      v = o(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

  def test_0e(self):
    shapereg = Reg(0x0e)
    periodreg = Reg(3)
    o = EnvOsc(periodreg, shapereg)
    v = o(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
    v = o(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
    v = o(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

  def test_0f(self):
    for shape in xrange(0x04, 0x08):
      o = EnvOsc(Reg(3), Reg(shape))
      v = o(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
      self.assertEqual([0] * (8 * 3 * 34), o(Block(8 * 3 * 34)).tolist())

if __name__ == '__main__':
  unittest.main()
