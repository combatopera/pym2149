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

from . import V, D, E, _topitch, major
from ..util import outerzip
import unittest

class TestV(unittest.TestCase):

    def test_trivial(self):
        v = V('0')
        self.assertEqual(0, v[0])
        self.assertEqual(0, v[1])
        self.assertEqual(0, v[.5])

    def test_trivial2(self):
        v = V('2')
        self.assertEqual(2, v[0])
        self.assertEqual(2, v[1])
        self.assertEqual(2, v[.5])

    def test_slide(self):
        v = V('0/1 5/1')
        self.assertEqual(0, v[0])
        self.assertEqual(5, v[1])
        self.assertEqual(2.5, v[.5])
        self.assertEqual(2.5, v[1.5])

    def test_slide2(self):
        v = V('0/5 5/1')
        self.assertEqual(0, v[0])
        self.assertEqual(1, v[1])
        self.assertEqual(5, v[5])
        self.assertEqual(0, v[6])
        self.assertEqual(2.5, v[5.5])

    def test_short(self):
        v = V('.5x7/.5 8')
        self.assertEqual(7, v[0])
        self.assertEqual(7.5, v[.25])
        self.assertEqual(8, v[.5])

    def test_mul(self):
        v = V('5x0/1 5')
        self.assertEqual(0, v[0])
        self.assertEqual(0, v[4])
        self.assertEqual(2.5, v[4.5])
        self.assertEqual(5, v[5])

    def test_mul2(self):
        v = V('5x0/2 5')
        self.assertEqual(0, v[0])
        self.assertEqual(0, v[3])
        self.assertEqual(2.5, v[4])
        self.assertEqual(5, v[5])

    def test_mul3(self):
        v = V('5x/2 5')
        self.assertEqual(0, v[0])
        self.assertEqual(0, v[3])
        self.assertEqual(2.5, v[4])
        self.assertEqual(5, v[5])

    def test_step(self):
        v = V('1 2 3/1', step = 5)
        self.assertEqual(1, v[0])
        self.assertEqual(3, v[2])
        self.assertEqual(6, v[3])
        self.assertEqual(4.5, v[2.5])
        self.assertEqual(-4, v[-3])

    def test_step2(self):
        v = V('1 2 3/0', step = 5)
        self.assertEqual(1, v[0])
        self.assertEqual(3, v[2])
        self.assertEqual(6, v[3])
        self.assertEqual(3, v[2.5])
        self.assertEqual(-4, v[-3])

    def test_loop(self):
        v = V('1 2,3 4/1')
        self.assertEqual(1, v[0])
        self.assertEqual(2, v[1])
        self.assertEqual(3, v[2])
        self.assertEqual(4, v[3])
        self.assertEqual(3.5, v[3.5])
        self.assertEqual(3, v[4])
        self.assertEqual(4, v[5])

    def test_loop2(self):
        v = V('13/14,6') + V('.25')
        self.assertEqual(13.25, v[0])
        self.assertEqual(12.75, v[1])
        self.assertEqual(6.75, v[13])
        self.assertEqual(6.25, v[14])
        self.assertEqual(6.25, v[15])
        self.assertEqual(6.25, v[100])

    def test_bias(self):
        v = V('13//12 10/1')
        self.assertEqual(13.375, v[.5])
        self.assertEqual(13.125, v[1.5])
        self.assertEqual(12.875, v[2.5])
        self.assertEqual(12.625, v[3.5])
        self.assertEqual(10.875, v[10.5])
        self.assertEqual(10.625, v[11.5])
        self.assertEqual(10, v[12])
        self.assertEqual(11.5, v[12.5]) # Unbiased.
        self.assertEqual(13.375, v[13.5])
        self.assertEqual(13.125, v[14.5])

    def test_bias2(self):
        v = V('12//5,13')
        self.assertAlmostEqual(11.6, v[.5])
        self.assertAlmostEqual(11.8, v[1.5])
        self.assertAlmostEqual(12, v[2.5])
        self.assertAlmostEqual(12.2, v[3.5])
        self.assertAlmostEqual(12.4, v[4.5])
        self.assertAlmostEqual(13, v[5.5])
        self.assertAlmostEqual(13, v[6.5])
        self.assertAlmostEqual(13, v[7.5])
        self.assertAlmostEqual(13, v[99])

    def test_bias3(self):
        v = V('12//5,13') << 1
        self.assertAlmostEqual(11.6, v[-.5])
        self.assertAlmostEqual(11.8, v[.5])
        self.assertAlmostEqual(12, v[1.5])
        self.assertAlmostEqual(12.2, v[2.5])
        self.assertAlmostEqual(12.4, v[3.5])
        self.assertAlmostEqual(13, v[4.5])
        self.assertAlmostEqual(13, v[5.5])
        self.assertAlmostEqual(13, v[6.5])
        self.assertAlmostEqual(13, v[99])

    def test_doubleshift(self):
        v = (V('/100 100') >> -5).of(10) >> 1
        for x, y in outerzip([5, 5.1, 5.2, 5.3, 5.4], [v[i] for i in range(1, 6)]):
            self.assertAlmostEqual(x, y)

    def test_shiftstep(self):
        v = V('0 1 2', step = 3) >> -1
        self.assertEqual(0, v[-1])
        self.assertEqual(1, v[0])
        self.assertEqual(2, v[1])
        self.assertEqual(3, v[2])

class TestD(unittest.TestCase):

    def test_works(self):
        d = D('1 2 3 + 2+ - 2- ++ -- 2++ 2-- 3#+ 4bb-')
        self.assertEqual([0, 0, 0], list(d[0]))
        self.assertEqual([0, 1, 0], list(d[1]))
        self.assertEqual([0, 2, 0], list(d[2]))
        self.assertEqual([1, 0, 0], list(d[3]))
        self.assertEqual([1, 1, 0], list(d[4]))
        self.assertEqual([-1, 0, 0], list(d[5]))
        self.assertEqual([-1, 1, 0], list(d[6]))
        self.assertEqual([2, 0, 0], list(d[7]))
        self.assertEqual([-2, 0, 0], list(d[8]))
        self.assertEqual([2, 1, 0], list(d[9]))
        self.assertEqual([-2, 1, 0], list(d[10]))
        self.assertEqual([1, 2, 1], list(d[11]))
        self.assertEqual([-1, 3, -2], list(d[12]))

    def test_sum(self):
        d = D('1 2') + D('1 +')
        self.assertEqual([0, 0, 0], list(d[0]))
        self.assertEqual([1, 1, 0], list(d[1]))

    def test_belowone(self):
        d = D('2 1.125 1 .9 0 -.9 -1 -1.125 -2 -3')
        self.assertEqual([0, 1, 0], list(d[.5]))
        self.assertEqual([0, .125, 0], list(d[1.5]))
        self.assertEqual([0, 0, 0], list(d[2.5]))
        self.assertEqual([0, 0, 0], list(d[3.5]))
        self.assertEqual([0, 0, 0], list(d[4.5]))
        self.assertEqual([0, 0, 0], list(d[5.5]))
        self.assertEqual([0, 0, 0], list(d[6.5]))
        self.assertEqual([0, -.125, 0], list(d[7.5]))
        self.assertEqual([0, -1, 0], list(d[8.5]))
        self.assertEqual([0, -2, 0], list(d[9.5]))

    def test_inversions(self):
        invs = D('1/1 3/1 1/1 5/1').inversions()
        self.assertEqual(3, len(invs))
        xform = lambda i: [complex(*reversed(invs[i][x / 2][:2])) for x in range(8)]
        self.assertEqual([0, 1, 2, 1, 0, 2, 4, 2], xform(0))
        self.assertEqual([2, 3, 4, 3, 2, .5j+1, 1j, .5j+1], xform(1))
        self.assertEqual([4, .5j+2, 1j, .5j+2, 4, .5j+3, 1j+2, .5j+3], xform(2))

    def test_inversions2(self):
        invs = D('1/1 2x3/1 5/1 +/1').inversions()
        self.assertEqual(3, len(invs))
        xform = lambda i: [complex(*reversed(invs[i][x / 2][:2])) for x in range(10)]
        self.assertEqual([0, 1, 2, 2, 2, 3, 4, .5j+2, 1j, .5j], xform(0))
        self.assertEqual([2, 3, 4, 4, 4, .5j+2, 1j, 1j+1, 1j+2, .5j+2], xform(1))
        self.assertEqual([4, .5j+2, 1j, 1j, 1j, 1j+1, 1j+2, 1j+3, 1j+4, .5j+4], xform(2))

class TestE(unittest.TestCase):

    def test_works(self):
        e = E(None, '4x1 3/1 1')
        self.assertEqual(0, e[.9].absframe)
        self.assertEqual(1, e[1.9].absframe)
        self.assertEqual(2, e[2.9].absframe)
        self.assertEqual(3, e[3.9].absframe)
        self.assertEqual(4, e[5.9].absframe)
        self.assertEqual(6, e[6].absframe)
        self.assertEqual(6, e[6.9].absframe)
        self.assertEqual(7, e[7.9].absframe)

    def test_off(self):
        e = E(None, '/.5 /1.5 1')
        self.assertEqual(None, e[0].onframes)
        self.assertEqual(.5, e[.5].onframes)
        self.assertEqual(0, e[1].onframes)
        self.assertEqual(None, e[2.5].onframes)
        self.assertEqual(0, e[0].absframe)
        self.assertEqual(0, e[.4].absframe)
        self.assertEqual(.5, e[.5].absframe)
        self.assertEqual(.5, e[.9].absframe)
        self.assertEqual(1, e[1].absframe)
        self.assertEqual(1, e[2.4].absframe)
        self.assertEqual(2.5, e[2.5].absframe)

    def test_rests(self):
        e = E(None, '.5/ 1.5/ /')
        self.assertEqual(0, e[0].onframes)
        self.assertEqual(0, e[.5].onframes)
        self.assertEqual(0, e[2].onframes)
        self.assertEqual(0, e[3].onframes)
        self.assertEqual(0, e[0].absframe)
        self.assertEqual(0, e[.4].absframe)
        self.assertEqual(.5, e[.5].absframe)
        self.assertEqual(.5, e[1.9].absframe)
        self.assertEqual(2, e[2].absframe)
        self.assertEqual(2, e[2.9].absframe)
        self.assertEqual(3, e[3].absframe)

    def test_absframe(self):
        e = E(None, '1 1 1')
        self.assertEqual(0, e[.5].absframe)
        self.assertEqual(1, e[1.1].absframe)
        self.assertEqual(2, e[2].absframe)
        self.assertEqual(3, e[3].absframe)
        self.assertEqual(500, e[500.9].absframe)

    def test_rshift(self):
        e = E(None, '3') >> 2
        self.assertEqual(-1, e[0].absframe)
        self.assertEqual(-1, e[1.9].absframe)
        self.assertEqual(2, e[2].absframe)
        self.assertEqual(2, e[4.9].absframe)
        self.assertEqual(5, e[5].absframe)
        self.assertEqual(5, e[7.9].absframe)

    def test_pipe(self):
        e = E(None, '2x2')
        f = E(None, '3x')
        s = e | f
        self.assertEqual(0, s[1.9].absframe)
        self.assertEqual(2, s[3.9].absframe)
        self.assertEqual(4, s[4.9].absframe)
        self.assertEqual(5, s[5.9].absframe)
        self.assertEqual(6, s[6.9].absframe)
        self.assertEqual(7, s[8.9].absframe)
        self.assertEqual(9, s[10.9].absframe)
        self.assertEqual(11, s[11.9].absframe)
        self.assertEqual(12, s[12.9].absframe)
        self.assertEqual(13, s[13.9].absframe)
        self.assertEqual(14, s[14].absframe)

    def test_pipe2(self):
        e = E(None, '3x')
        f = E(None, '2.5')
        s = e | f
        self.assertEqual(0, s[0.9].absframe)
        self.assertEqual(1, s[1.9].absframe)
        self.assertEqual(2, s[2.9].absframe)
        self.assertEqual(3, s[5.4].absframe)
        self.assertEqual(5.5, s[6.4].absframe)
        self.assertEqual(6.5, s[7.4].absframe)
        self.assertEqual(7.5, s[8.4].absframe)
        self.assertEqual(8.5, s[10.9].absframe)
        self.assertEqual(11, s[11].absframe)

    def test_pipe3(self):
        e = E(None, '2x')
        f = E(None, '2x2')
        g = E(None, '2x.5')
        s = e | f | g
        self.assertEqual(0, s[.9].absframe)
        self.assertEqual(1, s[1.9].absframe)
        self.assertEqual(2, s[3.9].absframe)
        self.assertEqual(4, s[5.9].absframe)
        self.assertEqual(6, s[6.4].absframe)
        self.assertEqual(6.5, s[6.9].absframe)
        self.assertEqual(7, s[7.9].absframe)
        self.assertEqual(8, s[8.9].absframe)
        self.assertEqual(9, s[10.9].absframe)
        self.assertEqual(11, s[12.9].absframe)
        self.assertEqual(13, s[13.4].absframe)
        self.assertEqual(13.5, s[13.9].absframe)
        self.assertEqual(14, s[14].absframe)

class TestInit(unittest.TestCase):

    def test_modes(self):
        self.assertEqual([60, 62, 64, 65, 67, 69, 71, 72], [_topitch(major, 1, 60, [0, d, 0]) for d in range(8)])
        self.assertEqual([60, 62, 63, 65, 67, 69, 70, 72], [_topitch(major, 2, 60, [0, d, 0]) for d in range(8)])
        self.assertEqual([60, 61, 63, 65, 67, 68, 70, 72], [_topitch(major, 3, 60, [0, d, 0]) for d in range(8)])
        self.assertEqual([60, 62, 64, 66, 67, 69, 71, 72], [_topitch(major, 4, 60, [0, d, 0]) for d in range(8)])
