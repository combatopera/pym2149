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

from .pitch import Pitch, Meantone, FiveLimit
from types import SimpleNamespace
import unittest, math

class TestMeantone(unittest.TestCase):

    def test_pythagoreanmodified(self):
        m = Meantone(SimpleNamespace(referencefrequency = 15552, referencemidinote = 60.25, meantoneflats = 5, meantonecomma = 0))
        def freqpitch(a):
            # Pitches:
            a(2048, 25.25)
            a(3072, 32.25)
            a(4608, 39.25)
            a(6912, 46.25)
            a(10368, 53.25)
            a(15552, 60.25)
            a(23328, 67.25)
            a(34992, 74.25)
            a(52488, 81.25)
            a(78732, 88.25)
            a(118098, 95.25)
            a(177147, 102.25)
            # Octaves:
            a(1024, 13.25)
            a(4096, 37.25)
            a(88573.5, 90.25)
            a(354294, 114.25)
            # Extremes:
            a(486, .25)
            a(746496, 127.25)
            # Interpolation:
            a(13824 * 2 ** (math.log(14762.25 / 13824, 2) * .75), 59)
            a(14762.25 * 2 ** (math.log(15552 / 14762.25, 2) * .75), 60)
        freqpitch(lambda freq, pitch: self.assertEqual(freq, m.freq(pitch)))
        freqpitch(lambda freq, pitch: self.assertEqual(pitch, m.pitch(freq)))
        # Fifths:
        self.assertEqual(1.5, m.freq(19.25) / m.freq(12.25))
        self.assertEqual(1.5, m.freq(20.25) / m.freq(13.25))
        self.assertEqual(1.5, m.freq(21.25) / m.freq(14.25))
        self.assertEqual(1.5, m.freq(22.25) / m.freq(15.25))
        self.assertEqual(1.5, m.freq(23.25) / m.freq(16.25))
        self.assertEqual(1.5, m.freq(24.25) / m.freq(17.25))
        self.assertEqual(2 ** 18 / 3 ** 11, m.freq(25.25) / m.freq(18.25)) # Comma.
        self.assertEqual(1.5, m.freq(26.25) / m.freq(19.25))
        self.assertEqual(1.5, m.freq(27.25) / m.freq(20.25))
        self.assertEqual(1.5, m.freq(28.25) / m.freq(21.25))
        self.assertEqual(1.5, m.freq(29.25) / m.freq(22.25))
        self.assertEqual(1.5, m.freq(30.25) / m.freq(23.25))

    def test_pythagoreanclassic(self):
        'This is the classic Eb x G# tuning.'
        m = Meantone(SimpleNamespace(referencefrequency = 200, referencemidinote = 53, meantoneflats = 2, meantonecomma = 0))
        self.assertEqual(2 ** 18 / 3 ** 11, m.freq(63) / m.freq(56))

    def test_meantonemajor(self):
        m = Meantone(SimpleNamespace(referencefrequency = 440, referencemidinote = 69, meantoneflats = 2, meantonecomma = .25))
        self.assertEqual(8, sum(1 for p in range(60, 72) if math.isclose(5 / 4, m.freq(p + 4) / m.freq(p))))

    def test_meantoneminor(self):
        m = Meantone(SimpleNamespace(referencefrequency = 440, referencemidinote = 69, meantoneflats = 2, meantonecomma = 1 / 3))
        self.assertEqual(9, sum(1 for p in range(60, 72) if math.isclose(6 / 5, m.freq(p + 3) / m.freq(p))))

class TestFiveLimit(unittest.TestCase):

    def test_asymmetric(self):
        t = FiveLimit(SimpleNamespace(referencefrequency = 440, referencemidinote = 69))
        self.assertAlmostEqual(440, t.freq(69))
        self.assertAlmostEqual(440 * 16 / 15, t.freq(70))
        self.assertAlmostEqual(440 * 9 / 8, t.freq(71))
        self.assertAlmostEqual(440 * 6 / 5, t.freq(72))
        self.assertAlmostEqual(440 * 5 / 4, t.freq(73))
        self.assertAlmostEqual(440 * 4 / 3, t.freq(74))
        self.assertAlmostEqual(440 * 45 / 32, t.freq(75))
        self.assertAlmostEqual(440 * 3 / 2, t.freq(76))
        self.assertAlmostEqual(440 * 8 / 5, t.freq(77))
        self.assertAlmostEqual(440 * 5 / 3, t.freq(78))
        self.assertAlmostEqual(440 * 9 / 5, t.freq(79))
        self.assertAlmostEqual(440 * 15 / 8, t.freq(80))

class TestPitch(unittest.TestCase):

    def test_str(self):
        self.assertEqual('C..4   ', str(Pitch(60)))
        self.assertEqual('C#.4   ', str(Pitch(61)))
        self.assertEqual('B..3   ', str(Pitch(59)))
        self.assertEqual('B..3+40', str(Pitch(59.4)))
        self.assertEqual('C..4-40', str(Pitch(59.6)))
        self.assertEqual('B..3+50', str(Pitch(59.5)))
        self.assertEqual('C..0   ', str(Pitch(12)))
        self.assertEqual('B.-1   ', str(Pitch(11)))
        self.assertEqual('B..9   ', str(Pitch(131)))
        self.assertEqual('C.10   ', str(Pitch(132)))
