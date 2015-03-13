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

from program import DefaultNote, FX
from collections import namedtuple
import unittest

class TestFX(unittest.TestCase):

    def test_modulation(self):
        fx = FX(namedtuple('Config', 'pitchbendpersemitone')(None))
        self.assertEqual(.5, fx.relmodulation())
        fx.modulation = 0
        self.assertEqual(0, fx.relmodulation())
        fx.modulation = 1
        self.assertEqual(0, fx.relmodulation())
        fx.modulation = 0x2000
        self.assertEqual(.5, fx.relmodulation())
        fx.modulation = 0x3fff
        self.assertEqual(1, fx.relmodulation())

    def test_pan(self):
        fx = FX(namedtuple('Config', 'pitchbendpersemitone')(None))
        self.assertEqual(0, fx.normpan())
        fx.pan = -0x2000
        self.assertEqual(-1, fx.normpan())
        fx.pan = -0x1fff
        self.assertEqual(-1, fx.normpan())
        fx.pan = 0
        self.assertEqual(0, fx.normpan())
        fx.pan = 0x1fff
        self.assertEqual(1, fx.normpan())

class TestDefaultNote(unittest.TestCase):

    def test_fadeout(self):
        self.assertEqual(sum([[i, i] for i in xrange(-1, -16, -1)], []), DefaultNote.fadeout.render())

if __name__ == '__main__':
    unittest.main()
