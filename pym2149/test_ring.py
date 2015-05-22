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

import unittest, numpy as np
from buf import Buf
from ring import SimpleRing, DerivativeRing

class TestRing(unittest.TestCase):

    def test_putring(self):
        b = Buf(np.zeros(20))
        r = SimpleRing.fromiter(int, xrange(5), 0).newcursor()
        r.index = 4
        r.putstrided(b, 3, 2, 8)
        self.assertEqual([0, 0, 0, 4, 0, 0, 0, 1, 0, 2, 0, 3, 0, 4, 0, 0, 0, 1, 0, 0], b.tolist())
        self.assertEqual(2, r.index)
        r.index = 4
        r.putstrided(b, 4, 2, 8)
        self.assertEqual([0, 0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, 1, 1, 0], b.tolist())
        self.assertEqual(2, r.index)

    def test_loop(self):
        b = Buf(np.zeros(20))
        r = SimpleRing.fromiter(int, xrange(5), 2).newcursor()
        r.index = 1
        r.putstrided(b, 3, 2, 8)
        self.assertEqual([0, 0, 0, 1, 0, 2, 0, 3, 0, 4, 0, 2, 0, 3, 0, 4, 0, 2, 0, 0], b.tolist())
        self.assertEqual(3, r.index)
        r.index = 1
        r.putstrided(b, 4, 2, 8)
        self.assertEqual([0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 2, 2, 3, 3, 4, 4, 2, 2, 0], b.tolist())
        self.assertEqual(3, r.index)

    def test_putringops(self):
        r = SimpleRing.fromiter(int, [0] * 5, None)
        self.assertEqual(0, Buf.putringops(r, None, 0))
        self.assertEqual(1, Buf.putringops(r, 0, 1))
        self.assertEqual(1, Buf.putringops(r, 4, 1))
        self.assertEqual(1, Buf.putringops(r, 0, 5))
        r.loopstart = 0
        self.assertEqual(2, Buf.putringops(r, 0, 6))
        self.assertEqual(2, Buf.putringops(r, 1, 5))
        self.assertEqual(2, Buf.putringops(r, 0, 10))
        r.loopstart = 1
        self.assertEqual(2, Buf.putringops(r, 0, 9))
        self.assertEqual(3, Buf.putringops(r, 0, 10))
        r.loopstart = 2
        self.assertEqual(3, Buf.putringops(r, 3, 8))
        self.assertEqual(4, Buf.putringops(r, 3, 9))

    def test_todiffring(self):
        unit = [1, 0, 1, 0]
        r = DerivativeRing(unit)
        self.assertEqual([1, -1, 1, -1, 1], list(r.buf))
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        unit = [1, 0, 1, 3]
        r = DerivativeRing(unit)
        self.assertEqual([1, -1, 1, 2, -2], list(r.buf))
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        unit = [1, 0, 1, 0, 1]
        r = DerivativeRing(unit)
        self.assertEqual([1, -1, 1, -1, 1, 0], list(r.buf))
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        unit = [2, 0, 1, 0, 1]
        r = DerivativeRing(unit)
        self.assertEqual([2, -2, 1, -1, 1, 1], list(r.buf))
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])

    def test_todiffringwithprolog(self):
        prolog = [1, 1, 0]
        unit = [0, 0]
        r = DerivativeRing(prolog + unit, len(prolog))
        self.assertEqual([1, 0, -1, 0, 0, 0], list(r.buf))
        self.assertEqual(4, r.loopstart)
        self.assertEqual(prolog + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(prolog + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        prolog = [1, 1]
        unit = [0, 0, 0]
        r = DerivativeRing(prolog + unit, len(prolog))
        self.assertEqual([1, 0, -1, 0, 0, 0], list(r.buf))
        self.assertEqual(3, r.loopstart)
        self.assertEqual(prolog + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(prolog + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        prolog = [1]
        unit = [1, 0, 0, 0]
        r = DerivativeRing(prolog + unit, len(prolog))
        self.assertEqual([1, 0, -1, 0, 0, 1], list(r.buf))
        self.assertEqual(2, r.loopstart)
        self.assertEqual(prolog + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(prolog + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        prolog = [1]
        unit = [1, 0, 0, 1]
        r = DerivativeRing(prolog + unit, len(prolog))
        self.assertEqual([1, 0, -1, 0, 1, 0], list(r.buf))
        self.assertEqual(2, r.loopstart)
        self.assertEqual(prolog + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(prolog + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])

def integrateringthrice(r):
    last = 0
    v = []
    index = 0
    for _ in xrange(3):
        while index < r.limit:
            v.append(last + r.buf[index])
            last = v[-1]
            index += 1
        index = r.loopstart
    return v

if '__main__' == __name__:
    unittest.main()