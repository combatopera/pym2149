#!/usr/bin/env python

# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import unittest, lfsr, time
from osc import ToneOsc, NoiseOsc, EnvOsc
from nod import Block
from reg import Reg

class TestToneOsc(unittest.TestCase):

  def test_works(self):
    o = ToneOsc(8, Reg(3))
    v = o.call(Block(96)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:48])
    self.assertEqual([1] * 24, v[48:72])
    self.assertEqual([0] * 24, v[72:])
    v = o.call(Block(48)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0] * 24, v[24:])

  def test_resume(self):
    o = ToneOsc(8, Reg(3))
    v = o.call(Block(25)).tolist()
    self.assertEqual([1] * 24, v[:24])
    self.assertEqual([0], v[24:])
    v = o.call(Block(24)).tolist()
    self.assertEqual([0] * 23, v[:23])
    self.assertEqual([1], v[23:])

  def test_carry(self):
    r = Reg(0x01)
    size = 3 * 8 + 1
    ref = ToneOsc(8, r).call(Block(size)).tolist()
    for n in xrange(size + 1):
      o = ToneOsc(8, r)
      v1 = o.call(Block(n)).tolist()
      v2 = o.call(Block(size - n)).tolist()
      self.assertEqual(ref, v1 + v2)

  def test_increaseperiodonboundary(self):
    r = Reg(0x01)
    o = ToneOsc(8, r)
    self.assertEqual([1] * 8 + [0] * 8, o.call(Block(16)).tolist())
    r.value = 0x02
    self.assertEqual([1] * 16 + [0] * 15, o.call(Block(31)).tolist())
    r.value = 0x03
    self.assertEqual([0] * 9 + [1] * 24 + [0], o.call(Block(34)).tolist())

  def test_decreaseperiodonboundary(self):
    r = Reg(0x03)
    o = ToneOsc(8, r)
    self.assertEqual([1] * 24 + [0] * 24, o.call(Block(48)).tolist())
    r.value = 0x02
    self.assertEqual([1] * 16 + [0] * 16 + [1] * 6, o.call(Block(38)).tolist())
    r.value = 0x01
    self.assertEqual([1] * 2 + [0] * 8 + [1] * 8 + [0], o.call(Block(19)).tolist())

  def test_smallerblocksthanperiod(self):
    r = Reg(0x05)
    o = ToneOsc(1, r)
    self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
    self.assertEqual([1,0,0,0], o.call(Block(4)).tolist())
    self.assertEqual([0,0,1], o.call(Block(3)).tolist())
    self.assertEqual([1,1,1,1], o.call(Block(4)).tolist())
    self.assertEqual([0,0,0,0,0], o.call(Block(5)).tolist())
    self.assertEqual([1], o.call(Block(1)).tolist())

  def test_performance(self):
    blockrate = 50
    blocksize = 2000000 // blockrate
    for p in 0x001, 0xfff:
      r = Reg(p)
      o = ToneOsc(8, r)
      start = time.time()
      for _ in xrange(blockrate):
        o.call(Block(blocksize))
      self.assertTrue(time.time() - start < .05)

class TestNoiseOsc(unittest.TestCase):

  def test_works(self):
    n = 100
    o = NoiseOsc(8, Reg(3))
    u = lfsr.Lfsr(*lfsr.ym2149nzdegrees)
    for _ in xrange(2):
      v = o.call(Block(48 * n)).tolist()
      for i in xrange(n):
        self.assertEqual([u()] * 48, v[i * 48:(i + 1) * 48])

  def test_carry(self):
    r = Reg(0x01)
    size = 17 * 16 + 1
    ref = NoiseOsc(8, r).call(Block(size)).tolist()
    for n in xrange(size + 1):
      o = NoiseOsc(8, r)
      v1 = o.call(Block(n)).tolist()
      v2 = o.call(Block(size - n)).tolist()
      self.assertEqual(ref, v1 + v2)

  def test_performance(self):
    blockrate = 50
    blocksize = 2000000 // blockrate
    for p in 0x01, 0x1f:
      r = Reg(p)
      o = NoiseOsc(8, r)
      start = time.time()
      for _ in xrange(blockrate):
        o.call(Block(blocksize))
      self.assertTrue(time.time() - start < .05)

class TestEnvOsc(unittest.TestCase):

  def test_values(self):
    v = EnvOsc.values0c
    self.assertEqual(1024, v.buf.shape[0])
    self.assertEqual(0, v.loop)
    self.assertEqual(range(32) + range(32), list(v.buf[:64]))
    v = EnvOsc.values08
    self.assertEqual(1024, v.buf.shape[0])
    self.assertEqual(0, v.loop)
    self.assertEqual(range(31, -1, -1) + range(31, -1, -1), list(v.buf[:64]))
    v = EnvOsc.values0e
    self.assertEqual(1024, v.buf.shape[0])
    self.assertEqual(0, v.loop)
    self.assertEqual(range(32) + range(31, -1, -1) + range(32), list(v.buf[:96]))
    v = EnvOsc.values0a
    self.assertEqual(1024, v.buf.shape[0])
    self.assertEqual(0, v.loop)
    self.assertEqual(range(31, -1, -1) + range(32) + range(31, -1, -1), list(v.buf[:96]))
    v = EnvOsc.values0f
    self.assertEqual(1032, v.buf.shape[0])
    self.assertEqual(32, v.loop)
    self.assertEqual(range(32) + [0] * 32, list(v.buf[:64]))
    v = EnvOsc.values0d
    self.assertEqual(1032, v.buf.shape[0])
    self.assertEqual(32, v.loop)
    self.assertEqual(range(32) + [31] * 32, list(v.buf[:64]))
    v = EnvOsc.values0b
    self.assertEqual(1032, v.buf.shape[0])
    self.assertEqual(32, v.loop)
    self.assertEqual(range(31, -1, -1) + [31] * 32, list(v.buf[:64]))
    v = EnvOsc.values09
    self.assertEqual(1032, v.buf.shape[0])
    self.assertEqual(32, v.loop)
    self.assertEqual(range(31, -1, -1) + [0] * 32, list(v.buf[:64]))

  def test_reset(self):
    shapereg = Reg(0x0c)
    periodreg = Reg(0x0001)
    o = EnvOsc(8, periodreg, shapereg)
    self.assertEqual(range(32) + range(16), o.call(Block(48 * 8)).tolist()[::8])
    self.assertEqual(range(16, 32) + range(16), o.call(Block(32 * 8)).tolist()[::8])
    shapereg.value = 0x0c
    self.assertEqual(range(32) + range(16), o.call(Block(48 * 8)).tolist()[::8])

  def test_08(self):
    shapereg = Reg(0x08)
    periodreg = Reg(3)
    o = EnvOsc(8, periodreg, shapereg)
    for _ in xrange(2):
      v = o.call(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

  def test_09(self):
    for shape in xrange(0x04):
      o = EnvOsc(8, Reg(3), Reg(shape))
      v = o.call(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
      self.assertEqual([0] * (8 * 3 * 34), o.call(Block(8 * 3 * 34)).tolist())

  def test_0a(self):
    shapereg = Reg(0x0a)
    periodreg = Reg(3)
    o = EnvOsc(8, periodreg, shapereg)
    v = o.call(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
    v = o.call(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
    v = o.call(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])

  def test_0c(self):
    shapereg = Reg(0x0c)
    periodreg = Reg(3)
    o = EnvOsc(8, periodreg, shapereg)
    for _ in xrange(2):
      v = o.call(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

  def test_0e(self):
    shapereg = Reg(0x0e)
    periodreg = Reg(3)
    o = EnvOsc(8,periodreg, shapereg)
    v = o.call(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
    v = o.call(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([31 - i] * 24, v[i * 24:(i + 1) * 24])
    v = o.call(Block(8 * 3 * 32)).tolist()
    for i in xrange(32):
      self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])

  def test_0f(self):
    for shape in xrange(0x04, 0x08):
      o = EnvOsc(8, Reg(3), Reg(shape))
      v = o.call(Block(8 * 3 * 32)).tolist()
      for i in xrange(32):
        self.assertEqual([i] * 24, v[i * 24:(i + 1) * 24])
      self.assertEqual([0] * (8 * 3 * 34), o.call(Block(8 * 3 * 34)).tolist())

if __name__ == '__main__':
  unittest.main()
