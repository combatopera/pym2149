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

class TestPhysicalRegisters(unittest.TestCase):

    chipchannels = 1
    maxtoneperiod = 0xfff
    maxnoiseperiod = 0x1f
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
        # Ignore high nibble:
        pr.R[1].value = 0x10
        self.assertEqual(0x021, lr.toneperiods[0].value)
        pr.R[1].value = 0xf0
        self.assertEqual(0x021, lr.toneperiods[0].value)
        pr.R[1].value = 0xff
        self.assertEqual(0xf21, lr.toneperiods[0].value)

    def test_noiseperiodmask(self):
        lr = LogicalRegisters(self, self, minnoiseperiod = None)
        pr = PhysicalRegisters(self, lr)
        self.assertEqual(0x00, lr.noiseperiod.value)
        pr.R[6].value = 0x1f
        self.assertEqual(0x1f, lr.noiseperiod.value)
        # Ignore 3 most significant bits:
        pr.R[6].value = 0x20
        self.assertEqual(0x00, lr.noiseperiod.value)
        pr.R[6].value = 0xe0
        self.assertEqual(0x00, lr.noiseperiod.value)
        pr.R[6].value = 0xff
        self.assertEqual(0x1f, lr.noiseperiod.value)

    def test_envshapemask(self):
        lr = LogicalRegisters(self, self)
        pr = PhysicalRegisters(self, lr)
        self.assertEqual(0x0, lr.envshape.value)
        pr.R[13].value = 0x0f
        self.assertEqual(0xf, lr.envshape.value)
        pr.R[13].value = 0x10
        self.assertEqual(0x0, lr.envshape.value)
        pr.R[13].value = 0xf0
        self.assertEqual(0x0, lr.envshape.value)
        pr.R[13].value = 0xff
        self.assertEqual(0xf, lr.envshape.value)

    def test_levelmask(self):
        lr = LogicalRegisters(self, self)
        pr = PhysicalRegisters(self, lr)
        self.assertEqual(0x0, lr.fixedlevels[0].value)
        pr.R[8].value = 0x0f
        self.assertEqual(0xf, lr.fixedlevels[0].value)
        pr.R[8].value = 0x10
        self.assertEqual(0x0, lr.fixedlevels[0].value)
        pr.R[8].value = 0xf0
        self.assertEqual(0x0, lr.fixedlevels[0].value)
        pr.R[8].value = 0xff
        self.assertEqual(0xf, lr.fixedlevels[0].value)
