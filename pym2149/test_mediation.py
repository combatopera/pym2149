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

from .mediation import DynamicMediation
from types import SimpleNamespace
import unittest

class TestDynamicMediation(unittest.TestCase):

    def setUp(self):
        self.warns = []
        self.m = DynamicMediation(SimpleNamespace(midichannelbase = 1, chipchannels = 3))
        self.m.warn = self.warn

    def warn(self, *args):
        self.warns.append(args)

    def tearDown(self):
        self.assertEqual([], self.warns)

    def acquire(self, *args):
        return self.m.acquirechipchan(*args)

    def release(self, *args):
        return self.m.releasechipchan(*args)

    def test_normalcase(self):
        # First-come first-served:
        self.assertEqual(0, self.acquire(1, 60, 0))
        self.assertEqual(1, self.acquire(2, 60, 1))
        self.assertEqual(2, self.acquire(3, 60, 2))
        # Chip channels are scarce, so go ahead and abort note-offs:
        self.assertEqual(0, self.release(1, 60))
        self.assertEqual(0, self.acquire(1, 61, 3))
        self.assertEqual(1, self.release(2, 60))
        self.assertEqual(1, self.acquire(2, 61, 4))
        self.assertEqual(2, self.release(3, 60))
        self.assertEqual(2, self.acquire(3, 61, 5))
        # MIDI 3 should reuse chip channel 2:
        self.assertEqual(2, self.release(3, 61))
        self.assertEqual(2, self.acquire(3, 62, 6))
        # MIDI 4 should use any spare chip channel:
        self.assertEqual(1, self.release(2, 61))
        self.assertEqual(1, self.acquire(4, 62, 7))

    def test_reusewhenthereisachoice(self):
        self.assertEqual(0, self.acquire(1, 60, 0))
        self.assertEqual(1, self.acquire(2, 60, 1))
        self.assertEqual(2, self.acquire(3, 60, 2))
        self.assertEqual(0, self.release(1, 60))
        self.assertEqual(1, self.release(2, 60))
        self.assertEqual(2, self.release(3, 60))
        # MIDI 2 should reuse chip channel 1:
        self.assertEqual(1, self.acquire(2, 60, 3))
        # MIDI 3 should reuse chip channel 2:
        self.assertEqual(2, self.acquire(3, 60, 4))

    def test_polyphony(self):
        # MIDI channel should only use as many chip channels as its current polyphony:
        self.assertEqual(0, self.acquire(1, 60, 0))
        self.assertEqual(1, self.acquire(1, 61, 1))
        self.assertEqual(0, self.release(1, 60))
        self.assertEqual(0, self.acquire(1, 60, 2))
        self.assertEqual(1, self.release(1, 61))
        self.assertEqual(1, self.acquire(1, 61, 3))

    def test_spuriousnoteon(self):
        self.assertEqual(0, self.acquire(1, 60, 0))
        # Simply return the already-acquired chip channel:
        self.assertEqual(0, self.acquire(1, 60, 1))

    def test_spuriousnoteoff(self):
        self.assertIs(None, self.m.releasechipchan(1, 60))

    def test_overload(self):
        self.assertEqual(0, self.acquire(1, 60, 0))
        self.assertEqual(1, self.acquire(2, 60, 1))
        self.assertEqual(2, self.acquire(3, 60, 2))
        self.assertEqual(0, self.release(1, 60))
        self.assertEqual(0, self.acquire(1, 61, 3))
        # Chip channel 1 had note-on least recently:
        self.assertEqual([], self.warns)
        self.assertEqual(1, self.acquire(4, 60, 4))
        self.assertEqual((self.m.interruptingformat, 'B'), self.warns.pop(0))
        # Note-off for interrupted note is now spurious:
        self.assertIs(None, self.m.releasechipchan(2, 60))

    def test_overloadwhenthereisachoice(self):
        self.assertEqual(0, self.acquire(1, 60, 0))
        self.assertEqual(1, self.acquire(2, 60, 1))
        self.assertEqual(2, self.acquire(3, 60, 2))
        self.assertEqual(0, self.release(1, 60))
        self.assertEqual(1, self.release(2, 60))
        self.assertEqual(2, self.release(3, 60))
        # Make all 3 chip channels equally attractive time-wise:
        self.assertEqual(0, self.acquire(4, 60, 3))
        self.assertEqual(1, self.acquire(4, 61, 3))
        self.assertEqual(2, self.acquire(4, 62, 3))
        # Last chip channel for MIDI 2 was 1:
        self.assertEqual([], self.warns)
        self.assertEqual(1, self.acquire(2, 61, 4))
        self.assertEqual((self.m.interruptingformat, 'B'), self.warns.pop(0))
        # Note-off for interrupted note is now spurious:
        self.assertIs(None, self.m.releasechipchan(4, 61))
