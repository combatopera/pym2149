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

import unittest, mock
from mediation import Mediation

class TestMediation(unittest.TestCase):

    def setUp(self):
        self.warn = mock.Mock().warn
        self.m = Mediation(3, warn = self.warn)

    def tearDown(self):
        self.assertEquals(0, self.warn.call_count)

    def test_normalcase(self):
        m = self.m
        # First-come first-served:
        self.assertEquals(0, m.acquirechipchan(1, 60, 0))
        self.assertEquals(1, m.acquirechipchan(2, 60, 1))
        self.assertEquals(2, m.acquirechipchan(3, 60, 2))
        # Chip channels are scarce, so go ahead and abort note-offs:
        self.assertEquals(0, m.releasechipchan(1, 60))
        self.assertEquals(0, m.acquirechipchan(1, 61, 3))
        self.assertEquals(1, m.releasechipchan(2, 60))
        self.assertEquals(1, m.acquirechipchan(2, 61, 4))
        self.assertEquals(2, m.releasechipchan(3, 60))
        self.assertEquals(2, m.acquirechipchan(3, 61, 5))
        # MIDI 3 should reuse chip channel 2:
        self.assertEquals(2, m.releasechipchan(3, 61))
        self.assertEquals(2, m.acquirechipchan(3, 62, 6))
        # MIDI 4 should use any spare chip channel:
        self.assertEquals(1, m.releasechipchan(2, 61))
        self.assertEquals(1, m.acquirechipchan(4, 62, 7))

    def test_reusewhenthereisachoice(self):
        m = self.m
        self.assertEquals(0, m.acquirechipchan(1, 60, 0))
        self.assertEquals(1, m.acquirechipchan(2, 60, 1))
        self.assertEquals(2, m.acquirechipchan(3, 60, 2))
        self.assertEquals(0, m.releasechipchan(1, 60))
        self.assertEquals(1, m.releasechipchan(2, 60))
        self.assertEquals(2, m.releasechipchan(3, 60))
        # MIDI 2 should reuse chip channel 1:
        self.assertEquals(1, m.acquirechipchan(2, 60, 3))
        # MIDI 3 should reuse chip channel 2:
        self.assertEquals(2, m.acquirechipchan(3, 60, 4))

    def test_polyphony(self):
        m = self.m
        # MIDI channel should only use as many chip channels as its current polyphony:
        self.assertEquals(0, m.acquirechipchan(1, 60, 0))
        self.assertEquals(1, m.acquirechipchan(1, 61, 1))
        self.assertEquals(0, m.releasechipchan(1, 60))
        self.assertEquals(0, m.acquirechipchan(1, 60, 2))
        self.assertEquals(1, m.releasechipchan(1, 61))
        self.assertEquals(1, m.acquirechipchan(1, 61, 3))

    def test_spuriousnoteon(self):
        m = self.m
        self.assertEquals(0, m.acquirechipchan(1, 60, 0))
        # Simply return the already-acquired chip channel:
        self.assertEquals(0, m.acquirechipchan(1, 60, 1))

    def test_spuriousnoteoff(self):
        m = self.m
        self.assertIs(None, m.releasechipchan(1, 60))

    def test_overload(self):
        m = self.m
        self.assertEquals(0, m.acquirechipchan(1, 60, 0))
        self.assertEquals(1, m.acquirechipchan(2, 60, 1))
        self.assertEquals(2, m.acquirechipchan(3, 60, 2))
        self.assertEquals(0, m.releasechipchan(1, 60))
        self.assertEquals(0, m.acquirechipchan(1, 61, 3))
        # Chip channel 1 had note-on least recently:
        self.assertEquals(0, self.warn.call_count)
        self.assertEquals(1, m.acquirechipchan(4, 60, 4))
        self.warn.assert_called_once_with(m.interruptingformat, 'B')
        self.warn.reset_mock()
        # Note-off for interrupted note is now spurious:
        self.assertIs(None, m.releasechipchan(2, 60))

    def test_overloadwhenthereisachoice(self):
        m = self.m
        self.assertEquals(0, m.acquirechipchan(1, 60, 0))
        self.assertEquals(1, m.acquirechipchan(2, 60, 1))
        self.assertEquals(2, m.acquirechipchan(3, 60, 2))
        self.assertEquals(0, m.releasechipchan(1, 60))
        self.assertEquals(1, m.releasechipchan(2, 60))
        self.assertEquals(2, m.releasechipchan(3, 60))
        # Make all 3 chip channels equally attractive time-wise:
        self.assertEquals(0, m.acquirechipchan(4, 60, 3))
        self.assertEquals(1, m.acquirechipchan(4, 61, 3))
        self.assertEquals(2, m.acquirechipchan(4, 62, 3))
        # Last chip channel for MIDI 2 was 1:
        self.assertEquals(0, self.warn.call_count)
        self.assertEquals(1, m.acquirechipchan(2, 61, 4))
        self.warn.assert_called_once_with(m.interruptingformat, 'B')
        self.warn.reset_mock()
        # Note-off for interrupted note is now spurious:
        self.assertIs(None, m.releasechipchan(4, 61))

if __name__ == '__main__':
    unittest.main()
