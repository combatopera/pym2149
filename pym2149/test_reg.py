# Copyright 2014, 2018, 2019 Andrzej Cichocki

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

import unittest
from .reg import Reg, VersionReg

class TestReg(unittest.TestCase):

    def test_bidi(self):
        high = Reg()
        low = Reg()
        value = Reg().link(lambda h, l: (h << 8) | l, high, low)
        high.link(lambda v: (v >> 8), value)
        low.link(lambda v: v & 0xff, value)
        vr = VersionReg().link(lambda v: v, value)
        value.link(lambda v: v, vr)
        self.assertEqual(0, vr.version)
        high.value = 0x87
        self.assertEqual(0x87, high.value)
        self.assertEqual(0, vr.version)
        low.value = 0x65
        self.assertEqual(0x87, high.value)
        self.assertEqual(0x65, low.value)
        self.assertEqual(0x8765, value.value)
        self.assertEqual(0x8765, vr.value)
        self.assertEqual(1, vr.version)
        value.value = 0x1234
        self.assertEqual(0x12, high.value)
        self.assertEqual(0x34, low.value)
        self.assertEqual(0x1234, value.value)
        self.assertEqual(0x1234, vr.value)
        self.assertEqual(2, vr.version)
        vr.value = 0x5678
        self.assertEqual(0x56, high.value)
        self.assertEqual(0x78, low.value)
        self.assertEqual(0x5678, value.value)
        self.assertEqual(0x5678, vr.value)
        self.assertEqual(3, vr.version)

    def test_mlink(self):
        reg = Reg()
        value = Reg().link(lambda r: r & 0xf, reg)
        reg.mlink(0xf, lambda v: v, value) # Only affect the low nibble.
        reg.value = 0xab
        self.assertEqual(0xab, reg.value)
        self.assertEqual(0xb, value.value)
        value.value = 0xcd
        self.assertEqual(0xad, reg.value)
        self.assertEqual(0xcd, value.value)

    def test_diamond(self):
        self.spectator = Reg(value = -1)
        self.lhs = Reg()
        self.rhs = Reg()
        self.pair = Reg()
        self.leaf = Reg().link(lambda l, r, s: (l, r, s), self.lhs, self.rhs, self.spectator)
        self.lhs.link(lambda p: p[0], self.pair)
        self.rhs.link(lambda p: p[1], self.pair)
        self.pair.value = 1, 2
        self.assertEqual((1, 2, -1), self.leaf.value)
        self.pair.value = 3, 4
        self.assertEqual((3, 4, -1), self.leaf.value)

    def test_multipath(self):
        source = Reg()
        middle = Reg().link(lambda x: x * 2, source)
        target1 = Reg().link(lambda x: x * 3, source).link(lambda x: x * 5, middle)
        target2 = Reg().link(lambda x: x * 7, middle).link(lambda x: x * 11, source)
        source.value = 1
        # These values have overwritten via-middle values:
        self.assertEqual(3, target1.value)
        self.assertEqual(11, target2.value)

    def test_initversionreg(self):
        self.assertEqual(0, VersionReg().version)
        self.assertEqual(1, VersionReg(value = 123).version)

    def test_minval(self):
        r = Reg(minval = 1, value = 0)
        self.assertEqual(1, r.value) # Check minval applied to passed-in value.
        r.value = 2
        self.assertEqual(2, r.value)
        r.value = 0
        self.assertEqual(1, r.value)

    def test_minval2(self):
        r = Reg(minval = 1, value = 2)
        self.assertEqual(2, r.value) # Check it's not always minval.
        that = Reg()
        r.link(lambda x: x, that)
        that.value = 5
        self.assertEqual(5, r.value)
        that.value = -1
        self.assertEqual(-1, that.value)
        self.assertEqual(1, r.value)
