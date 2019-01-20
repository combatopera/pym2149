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
from .timer import SimpleTimer, MinBlockRateTimer

class TestSimpleTimer(unittest.TestCase):

    def periodframecount(self, rate):
        block, = self.t.blocksforperiod(rate)
        return block.framecount

    def test_carry(self):
        clock = 2000000
        t = self.t = SimpleTimer(clock)
        self.assertEqual(33333, self.periodframecount(60))
        self.assertEqual(20, t.carryticks)
        self.assertEqual(33334, self.periodframecount(60))
        self.assertEqual(-20, t.carryticks)
        self.assertEqual(33333, self.periodframecount(60))
        self.assertEqual(0, t.carryticks)
        self.assertEqual(clock * 10, self.periodframecount(.1))
        self.assertEqual(0, t.carryticks)

    def test_fractionalrefreshrates(self):
        t = self.t = SimpleTimer(100)
        self.assertEqual(200, self.periodframecount(.5))
        self.assertEqual(0, t.carryticks)
        self.assertEqual(300, self.periodframecount(1 / 3))
        self.assertEqual(0, t.carryticks)
        self.assertEqual(67, self.periodframecount(1.5))
        self.assertEqual(-.5, t.carryticks)
        self.assertEqual(66, self.periodframecount(1.5))
        self.assertEqual(.5, t.carryticks)
        self.assertEqual(67, self.periodframecount(1.5))
        self.assertEqual(0, t.carryticks)

    def test_nonintegerclock(self):
        t = self.t = SimpleTimer(100.5)
        self.assertEqual(34, self.periodframecount(3))
        self.assertEqual(-1.5, t.carryticks)
        self.assertEqual(33, self.periodframecount(3))
        self.assertEqual(0, t.carryticks)
        self.assertEqual(34, self.periodframecount(3))
        self.assertEqual(-1.5, t.carryticks)
        t.carryticks = 0

class TestMinBlockRateTimer(unittest.TestCase):

    def test_minblockrate(self):
        t = MinBlockRateTimer(1000, 2)
        self.assertEqual([333], [b.framecount for b in t.blocksforperiod(3)])
        self.assertEqual(1, t.carryticks)
        self.assertEqual([334], [b.framecount for b in t.blocksforperiod(3)])
        self.assertEqual(-1, t.carryticks)
        self.assertEqual([333], [b.framecount for b in t.blocksforperiod(3)])
        self.assertEqual(0, t.carryticks)
        self.assertEqual([500], [b.framecount for b in t.blocksforperiod(2)])
        self.assertEqual(0, t.carryticks)
        self.assertEqual([500, 500], [b.framecount for b in t.blocksforperiod(1)])
        self.assertEqual(0, t.carryticks)
        # Don't bother returning a block of size zero:
        self.assertEqual([], [b.framecount for b in t.blocksforperiod(2001)])
        self.assertEqual(1000, t.carryticks)
        t.carryticks = 0

    def test_inexactminblockrate(self):
        t = MinBlockRateTimer(1000, 3)
        # Every block satisfies the given condition:
        self.assertEqual([333, 333, 333, 1], [b.framecount for b in t.blocksforperiod(1)])
        self.assertEqual(0, t.carryticks)
