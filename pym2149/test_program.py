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

from .program import DefaultNote, FX, Note
from collections import namedtuple
from .reg import Reg
import unittest

class TestFX(unittest.TestCase):

    def test_modulation(self):
        fx = FX(namedtuple('Config', 'pitchbendpersemitone')(None), False)
        self.assertEqual(.5, fx.relmodulation())
        fx.modulation.value = 0
        self.assertEqual(0, fx.relmodulation())
        fx.modulation.value = 1
        self.assertEqual(0, fx.relmodulation())
        fx.modulation.value = 0x2000
        self.assertEqual(.5, fx.relmodulation())
        fx.modulation.value = 0x3fff
        self.assertEqual(1, fx.relmodulation())

    def test_pan(self):
        fx = FX(namedtuple('Config', 'pitchbendpersemitone')(None), False)
        self.assertEqual(0, fx.normpan())
        fx.pan.value = -0x2000
        self.assertEqual(-1, fx.normpan())
        fx.pan.value = -0x1fff
        self.assertEqual(-1, fx.normpan())
        fx.pan.value = 0
        self.assertEqual(0, fx.normpan())
        fx.pan.value = 0x1fff
        self.assertEqual(1, fx.normpan())

class TestDefaultNote(unittest.TestCase):

    def test_fadeout(self):
        self.assertEqual(sum([[i, i] for i in range(-1, -16, -1)], []), DefaultNote.fadeout.render())

class TestNote(unittest.TestCase):

    def test_fixedlevel(self):
        toneperiods = [Reg()]
        toneflags = [None]
        noiseflags = [None]
        fixedlevels = [Reg()]
        levelmodes = [None]
        timers = [None]
        chip = namedtuple('Chip', 'toneperiods toneflags noiseflags fixedlevels levelmodes timers')(toneperiods, toneflags, noiseflags, fixedlevels, levelmodes, timers)
        note = Note(None, chip, 0, None, None, None, None)
        self.assertFalse(hasattr(fixedlevels[0], 'value'))
        note.fixedlevel = 7
        self.assertEqual(7, fixedlevels[0].value)
        note.fixedlevel = 0
        self.assertEqual(0, fixedlevels[0].value)
        note.fixedlevel = -1
        self.assertEqual(0, fixedlevels[0].value)
        note.fixedlevel = 15
        self.assertEqual(15, fixedlevels[0].value)
        note.fixedlevel = 16
        self.assertEqual(15, fixedlevels[0].value)
        # The chip never gains a reference:
        self.assertEqual([], fixedlevels[0].links)
