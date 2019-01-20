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
from .mfp import MFPTimer

class TestMFPTimer(unittest.TestCase):

    def test_setfreq(self):
        timer = MFPTimer()
        timer.freq.value = 1000
        self.assertEqual(2460, timer.getnormperiod()) # Close.
        timer.freq.value = 100
        self.assertEqual(24576, timer.getnormperiod()) # Exact.

    def test_zerotdr(self):
        t = MFPTimer()
        t.control_data.value = 3, 0
        self.assertEqual(300, t.getfreq())
        self.assertEqual((3, 0), t.findtcrtdr(300))
