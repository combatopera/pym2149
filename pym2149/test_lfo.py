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
from .lfo import LFO, FloatLFO

class TestLFO(unittest.TestCase):

    def test_works(self):
        self.assertEqual([5], LFO(5).render())
        self.assertEqual([8], LFO(5).jump(8).render())
        self.assertEqual([5, 8], LFO(5).lin(1, 8).render())
        self.assertEqual([5, 6, 7, 8], LFO(5).lin(3, 8).render())
        self.assertEqual([5, 7, 8], LFO(5).lin(2, 8).render())
        self.assertEqual([5, 6, 7, 7, 8], LFO(5).lin(4, 8).render())
        # Negative values:
        self.assertEqual([-5, -8], LFO(-5).lin(1, -8).render())
        self.assertEqual([-5, -6, -7, -8], LFO(-5).lin(3, -8).render())
        self.assertEqual([-5, -7, -8], LFO(-5).lin(2, -8).render())
        self.assertEqual([-5, -6, -7, -7, -8], LFO(-5).lin(4, -8).render())
        # Holds:
        self.assertEqual([5, 5, 5, 5, 6, 7, 8], LFO(5).hold(3).lin(3, 8).render())
        self.assertEqual([5, 5, 5, 8], LFO(5).hold(3).jump(8).render())
        self.assertEqual([True, True, True, False], LFO(True).hold(3).jump(False).render())
        # Literal:
        self.assertEqual([1, 2, 3, 4, 5], LFO(1).then(2, 3, 4, 5).render())
        self.assertEqual([1, 2, 3, 4, 6], LFO(1).then(2, 3, 4, 5).jump(6).render())
        # Triangular:
        # TODO: Should support rational period.
        self.assertEqual([5, 7, 5, 3, 5], LFO(5).tri(4, 1, 7).render()) # Simplest possible.
        self.assertEqual([5, 7, 5, 3, 5, 7, 5, 3, 5], LFO(5).tri(8, 1, 7).render())
        self.assertEqual([5, 6, 7, 6, 5, 4, 3, 4, 5], LFO(5).tri(8, 2, 7).render())
        self.assertEqual([5] + [6, 7, 6, 5, 4, 3, 4, 5] * 2, LFO(5).tri(16, 2, 7).render())
        self.assertEqual([5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5], LFO(5).tri(16, 4, 9).render())
        self.assertEqual([5, 7, 9, 7, 5, 3, 1, 3, 5, 7, 9, 7, 5, 3, 1, 3, 5], LFO(5).tri(16, 2, 9).render())
        # Infinite:
        lfo = LFO(5).hold(2).tri(8, 2, 7)
        self.assertEqual([5, 5, 5] + [6, 7, 6, 5, 4, 3, 4, 5] * 10, lfo.loop(8).render(83))
        self.assertEqual([5, 5, 5, 6, 7, 6, 5, 4, 3, 4, 5] + [7, 6, 5, 4, 3, 4, 5] * 10, lfo.loop(7).render(81))
        # Calling loop again overrides existing loop:
        lfo = LFO(5).lin(2, 7)
        self.assertEqual([5, 6, 7], lfo.render())
        self.assertEqual([5, 6, 7, 6, 7, 6, 7], lfo.loop(2).render(7))
        self.assertEqual([5, 6, 7, 5, 6, 7, 5], lfo.loop(2).loop(3).render(7))
        # Loop all:
        lfo = LFO(5).lin(2, 7).loop()
        self.assertEqual([5, 6, 7, 5, 6, 7, 5], lfo.render(7))
        lfo.then(8)
        self.assertEqual([5, 6, 7, 8, 5, 6, 7, 8, 5], lfo.render(9))

    def test_bias(self):
        self.assertEqual([1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6], LFO(1).lin(10, 6).render())
        self.assertEqual([-1, -2, -2, -3, -3, -4, -4, -5, -5, -6, -6], LFO(-1).lin(10, -6).render())
        self.assertEqual([6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1], LFO(6).lin(10, 1).render())
        self.assertEqual([-6, -5, -5, -4, -4, -3, -3, -2, -2, -1, -1], LFO(-6).lin(10, -1).render())
        self.assertEqual([2, 1, 1, 0, 0, -1, -1, -2, -2], LFO(2).lin(8, -2).render())
        self.assertEqual([-2, -1, -1, 0, 0, 1, 1, 2, 2], LFO(-2).lin(8, 2).render())

    def test_float(self):
        self.assertEqual([5, 5.5, 6, 6.5], FloatLFO(5).lin(3, 6.5).render())
