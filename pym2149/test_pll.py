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
from collections import namedtuple
from pll import PLL
import unittest, time, threading

class E(float): pass

class TestPLL(unittest.TestCase):

    updaterate = 50
    updateperiod = 1 / updaterate

    def lists(self, positionshift, *lists):
        pll = PLL(namedtuple('Config', 'updaterate pllalpha')(self.updaterate, .2))
        mark = time.time()
        for u, events in enumerate(lists):
            for event in events:
                pll.event(event, eventtime = mark + self.updateperiod * (u + .5) + event)
            # Simulate what the thread would do:
            positiontime = pll.getpositiontime(mark, u + 1)
            pll.closeupdate(positiontime)
        for u, events in enumerate(lists):
            for i, event in enumerate(events):
                self.assertIs(event, pll.updates[u][i])
            self.assertEqual(len(events), len(pll.updates[u]))
        self.assertEqual(len(lists), len(pll.updates))
        self.assertEqual(positionshift, round(positiontime - (mark + self.updateperiod * len(lists)), 6))

    def test_0perfecttiming(self):
        self.lists(0,
            [E(0)],
            [E(0)],
            [],
            [E(0)],
            [E(0), E(0)],
            [E(0)],
        )

    def test_1consistentlylate(self):
        self.lists(.005,
            [E(.005)],
            [E(.005)],
            [],
            [E(.005)],
            [E(.005), E(.005)],
            [E(.005)],
        )

    def test_2consistentlyearly(self):
        self.lists(-.005,
            [E(-.005)],
            [E(-.005)],
            [],
            [E(-.005)],
            [E(-.005), E(-.005)],
            [E(-.005)],
        )

if '__main__' == __name__:
    unittest.main()
