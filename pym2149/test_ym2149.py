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

from .ym2149 import LogicalRegisters, PhysicalRegisters
import unittest

class TestRegisters(unittest.TestCase):

    chipchannels = 1
    maxtoneperiod = 0xfff
    maxnoiseperiod = None
    maxenvperiod = None
    mintoneperiod = None

    def test_toneperiodmask(self):
        lr = LogicalRegisters(self, self)
        pr = PhysicalRegisters(self, lr)
        self.assertEqual(0x000, lr.toneperiods[0].value)
        pr.R[0].value = 0x21
        self.assertEqual(0x021, lr.toneperiods[0].value)
        pr.R[1].value = 0x03
        self.assertEqual(0x321, lr.toneperiods[0].value)
        pr.R[1].value = 0x0f
        self.assertEqual(0xf21, lr.toneperiods[0].value)
        pr.R[1].value = 0x10
        self.assertEqual(0x021, lr.toneperiods[0].value)
