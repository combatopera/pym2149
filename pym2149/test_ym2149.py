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
from ym2149 import ClockInfo
from collections import namedtuple

class TestYM2149(unittest.TestCase):

  def test_toneperiodclamp(self):
    Config = namedtuple('Config', 'nominalclock underclock')
    for underclock in 1, 8:
      nomclock = 2000000
      clock = nomclock // underclock
      def toneperiodclampor0(implclock, outrate):
        ci = ClockInfo(Config(nomclock, underclock))
        ci.implclock = implclock
        return ci.toneperiodclampor0(outrate)
      self.assertEqual(5, toneperiodclampor0(clock, 44100))
      # We shouldn't make Nyquist itself the clamp:
      self.assertEqual(4, toneperiodclampor0(clock, 50000))
      # But higher frequencies are acceptable:
      self.assertEqual(5, toneperiodclampor0(clock, 50000-1))
      self.assertEqual(5, toneperiodclampor0(clock+1, 50000))
      # Same again:
      self.assertEqual(9, toneperiodclampor0(clock, 25000))
      self.assertEqual(10, toneperiodclampor0(clock, 25000-1))
      self.assertEqual(10, toneperiodclampor0(clock+1, 25000))
      # Chip can sing higher than half these outrates:
      self.assertEqual(1, toneperiodclampor0(clock, 250000-1))
      self.assertEqual(1, toneperiodclampor0(clock+1, 250000))
      # But not half of this one:
      self.assertEqual(0, toneperiodclampor0(clock, 250000))

if __name__ == '__main__':
  unittest.main()
