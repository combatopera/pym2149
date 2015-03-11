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

import unittest
from lfo import LFO

class TestLFO(unittest.TestCase):

  def test_works(self):
    self.assertEqual([5], LFO(5))
    self.assertEqual([8], LFO(5).jump(8))
    self.assertEqual([5, 8], LFO(5).lin(1, 8))
    self.assertEqual([5, 6, 7, 8], LFO(5).lin(3, 8))
    self.assertEqual([5, 7, 8], LFO(5).lin(2, 8).round().render())
    self.assertEqual([5, 6, 7, 7, 8], LFO(5).lin(4, 8).round().render())
    # Negative values:
    self.assertEqual([-5, -8], LFO(-5).lin(1, -8))
    self.assertEqual([-5, -6, -7, -8], LFO(-5).lin(3, -8))
    self.assertEqual([-5, -7, -8], LFO(-5).lin(2, -8).round().render())
    self.assertEqual([-5, -6, -7, -7, -8], LFO(-5).lin(4, -8).round().render())
    # Holds:
    self.assertEqual([5, 5, 5, 5, 6, 7, 8], LFO(5).hold(3).lin(3, 8))
    self.assertEqual([5, 5, 5, 8], LFO(5).hold(3).jump(8))
    # Triangular:
    self.assertEqual([5, 7, 5, 3, 5], LFO(5).tri(4, 1, 7)) # Simplest possible.
    self.assertEqual([5, 7, 5, 3, 5, 7, 5, 3, 5], LFO(5).tri(8, 1, 7))
    self.assertEqual([5, 6, 7, 6, 5, 4, 3, 4, 5], LFO(5).tri(8, 2, 7))
    self.assertEqual([5] + [6, 7, 6, 5, 4, 3, 4, 5] * 2, LFO(5).tri(16, 2, 7))
    self.assertEqual([5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1, 2, 3, 4, 5], LFO(5).tri(16, 4, 9))
    self.assertEqual([5, 7, 9, 7, 5, 3, 1, 3, 5, 7, 9, 7, 5, 3, 1, 3, 5], LFO(5).tri(16, 2, 9))
    # Infinite:
    lfo = LFO(5).hold(2).tri(8, 2, 7)
    self.assertEqual([5, 5, 5] + [6, 7, 6, 5, 4, 3, 4, 5] * 10, lfo.loop(8).render(83))
    self.assertEqual([5, 5, 5, 6, 7, 6, 5, 4, 3, 4, 5] + [7, 6, 5, 4, 3, 4, 5] * 10, lfo.loop(7).render(81))

if __name__ == '__main__':
  unittest.main()
