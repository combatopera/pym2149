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
from ym2149 import toneperiodclampor0
from collections import namedtuple

class TestYM2149(unittest.TestCase):

  def test_toneperiodclamp(self):
    Chip = namedtuple('Chip', 'clock scale')
    for scale in 8, 1:
      clock = 2000000 // 8 * scale
      self.assertEqual(5, toneperiodclampor0(Chip(clock, scale), 44100))
      # We shouldn't make Nyquist itself the clamp:
      self.assertEqual(4, toneperiodclampor0(Chip(clock, scale), 50000))
      # But higher frequencies are acceptable:
      self.assertEqual(5, toneperiodclampor0(Chip(clock, scale), 50000-1))
      self.assertEqual(5, toneperiodclampor0(Chip(clock+1, scale), 50000))
      # Same again:
      self.assertEqual(9, toneperiodclampor0(Chip(clock, scale), 25000))
      self.assertEqual(10, toneperiodclampor0(Chip(clock, scale), 25000-1))
      self.assertEqual(10, toneperiodclampor0(Chip(clock+1, scale), 25000))
      # Chip can sing higher than half these outrates:
      self.assertEqual(1, toneperiodclampor0(Chip(clock, scale), 250000-1))
      self.assertEqual(1, toneperiodclampor0(Chip(clock+1, scale), 250000))
      # But not half of this one:
      self.assertEqual(0, toneperiodclampor0(Chip(clock, scale), 250000))

if __name__ == '__main__':
  unittest.main()
