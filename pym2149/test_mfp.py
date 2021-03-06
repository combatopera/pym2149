# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .dac import PWMEffect
from .mfp import MFPTimer
from unittest import TestCase

class TestMFPTimer(TestCase):

    def test_setfreq(self):
        timer = MFPTimer()
        timer.effect.value = PWMEffect
        timer.freq.value = 1000
        self.assertEqual(2460, timer._getnormperiod()) # Close.
        timer.freq.value = 100
        self.assertEqual(24576, timer._getnormperiod()) # Exact.

    def test_zerotdr(self):
        t = MFPTimer()
        t.effect.value = PWMEffect
        t.control_data.value = 3, 0
        self.assertEqual(300, t.getfreq())
        self.assertEqual((3, 0), t._findtcrtdr(300))

    def test_stop(self):
        t = MFPTimer()
        t.effect.value = PWMEffect
        t.freq.value = 1000
        self.assertEqual(10, t.prescalerornone.value)
        self.assertEqual(123, t.effectivedata.value)
        t.freq.value = 0
        self.assertEqual(None, t.prescalerornone.value)
        self.assertEqual(123, t.effectivedata.value)
