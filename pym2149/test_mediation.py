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
from mediation import Mediation

class TestMediation(unittest.TestCase):

    def test_normalcase(self):
        m = Mediation(3)
        # First-come first-served:
        self.assertEquals(0, m.acquirechipchan(1, 60))
        self.assertEquals(1, m.acquirechipchan(2, 60))
        self.assertEquals(2, m.acquirechipchan(3, 60))
        # Chip channels are scarce, so go ahead and abort note-offs:
        self.assertEquals(0, m.releasechipchan(1, 60))
        self.assertEquals(0, m.acquirechipchan(1, 61))
        self.assertEquals(1, m.releasechipchan(2, 60))
        self.assertEquals(1, m.acquirechipchan(2, 61))
        self.assertEquals(2, m.releasechipchan(3, 60))
        self.assertEquals(2, m.acquirechipchan(3, 61))
        # MIDI 3 should reuse chip channel 2:
        self.assertEquals(2, m.releasechipchan(3, 61))
        self.assertEquals(2, m.acquirechipchan(3, 62))
        # MIDI 4 should use any spare chip channel:
        self.assertEquals(1, m.releasechipchan(2, 61))
        self.assertEquals(1, m.acquirechipchan(4, 62))

    def test_polyphony(self):
        raise Exception('Implement me!')

    def test_spuriousnoteon(self):
        raise Exception('Implement me!')

    def test_spuriousnoteoff(self):
        raise Exception('Implement me!')

if __name__ == '__main__':
    unittest.main()
