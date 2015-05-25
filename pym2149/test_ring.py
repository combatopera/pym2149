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

import unittest, numpy as np, ring
from buf import Buf

class DerivativeRing(ring.DerivativeRing): minloopsize = 1

class TestDerivativeRing(unittest.TestCase):

    def test_minloopsize(self):
        class R(ring.DerivativeRing): pass
        for minloopsize in 7, 8, 9:
            R.minloopsize = minloopsize
            r = R(xrange(1, 7), 3)
            self.assertEqual(4, r.loopstart)
            self.assertEqual([1, 2, 3, 4, 5, 6, 4, 5, 6, 4, 5, 6, 4], r.dc)
            self.assertEqual([1, 1, 1, 1, 1, 1, -2, 1, 1, -2, 1, 1, -2], r.tolist())
        for minloopsize in 10, 11, 12:
            R.minloopsize = minloopsize
            r = R(xrange(1, 7), 3)
            self.assertEqual(4, r.loopstart)
            self.assertEqual([1, 2, 3, 4, 5, 6, 4, 5, 6, 4, 5, 6, 4, 5, 6, 4], r.dc)
            self.assertEqual([1, 1, 1, 1, 1, 1, -2, 1, 1, -2, 1, 1, -2, 1, 1, -2], r.tolist())

    def test_putstrided(self):
        b = Buf(np.empty(20))
        c = DerivativeRing(xrange(5)).newcursor()
        c.index = 4
        c.putstrided(b, 3, 2, 8)
        self.assertEqual([3, 0, 0, 1, 0, -4, 0, 1, 0, 1, 0, 1, 0, 1, 0, -4, 0, 1, 0, 0], b.tolist())
        b.integrate(b)
        self.assertEqual([3, 3, 3, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, 1, 1, 1], b.tolist())
        self.assertEqual(2, c.index)

    def test_putstridedwithintro(self):
        b = Buf(np.empty(20))
        c = DerivativeRing(xrange(5), 2).newcursor()
        c.index = 1
        c.putstrided(b, 3, 2, 8)
        self.assertEqual([0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, -2, 0, 1, 0, 1, 0, -2, 0, 0], b.tolist())
        b.integrate(b)
        self.assertEqual([0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 2, 2, 3, 3, 4, 4, 2, 2, 2], b.tolist())
        self.assertEqual(3, c.index)

    def test_data(self):
        unit = [1, 0, 1, 0]
        r = DerivativeRing(unit)
        self.assertEqual([1, -1, 1, -1, 1], r.tolist())
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        unit = [1, 0, 1, 3]
        r = DerivativeRing(unit)
        self.assertEqual([1, -1, 1, 2, -2], r.tolist())
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        unit = [1, 0, 1, 0, 1]
        r = DerivativeRing(unit)
        self.assertEqual([1, -1, 1, -1, 1, 0], r.tolist())
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        unit = [2, 0, 1, 0, 1]
        r = DerivativeRing(unit)
        self.assertEqual([2, -2, 1, -1, 1, 1], r.tolist())
        self.assertEqual(1, r.loopstart)
        self.assertEqual(unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])

    def test_datawithintro(self):
        intro = [1, 1, 0]
        unit = [0, 0]
        r = DerivativeRing(intro + unit, len(intro))
        self.assertEqual([1, 0, -1, 0, 0, 0], r.tolist())
        self.assertEqual(4, r.loopstart)
        self.assertEqual(intro + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(intro + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        intro = [1, 1]
        unit = [0, 0, 0]
        r = DerivativeRing(intro + unit, len(intro))
        self.assertEqual([1, 0, -1, 0, 0, 0], r.tolist())
        self.assertEqual(3, r.loopstart)
        self.assertEqual(intro + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(intro + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        intro = [1]
        unit = [1, 0, 0, 0]
        r = DerivativeRing(intro + unit, len(intro))
        self.assertEqual([1, 0, -1, 0, 0, 1], r.tolist())
        self.assertEqual(2, r.loopstart)
        self.assertEqual(intro + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(intro + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])
        intro = [1]
        unit = [1, 0, 0, 1]
        r = DerivativeRing(intro + unit, len(intro))
        self.assertEqual([1, 0, -1, 0, 1, 0], r.tolist())
        self.assertEqual(2, r.loopstart)
        self.assertEqual(intro + unit * 3 + unit[:1], integrateringthrice(r))
        self.assertEqual(intro + unit + unit[:1], [r.dc[x] for x in xrange(r.limit)])

def integrateringthrice(r):
    u = r.tolist()
    last = 0
    v = []
    index = 0
    for _ in xrange(3):
        while index < r.limit:
            v.append(last + u[index])
            last = v[-1]
            index += 1
        index = r.loopstart
    return v

if '__main__' == __name__:
    unittest.main()
