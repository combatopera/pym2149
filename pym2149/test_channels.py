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
from .channels import ControlPair, Channels

class TestControlPair(unittest.TestCase):

    def setUp(self):
        self.v = []

    def flush(self, midichan, value):
        self.v.append(value)

    def test_0shift(self):
        cp = ControlPair(0x2000, self.flush, 0)
        cp.setlsb(1, 0x00)
        cp.setmsb(1, 0x40)
        cp.setmsb(1, 0x3f)
        cp.setmsb(1, 0x41)
        cp.setlsb(1, 0x7f)
        cp.setmsb(1, 0x3f)
        self.assertEqual([0, -128, 128, 255, -1], self.v[1:])

    def test_7shift(self):
        cp = ControlPair(0x2000, self.flush, 7)
        cp.setlsb(1, 0x00)
        cp.setmsb(1, 0x40)
        cp.setmsb(1, 0x3f)
        cp.setmsb(1, 0x41)
        cp.setlsb(1, 0x7f)
        cp.setmsb(1, 0x3f)
        self.assertEqual([0, -1, 1, 1, -1], self.v[1:])

class TestChannels(unittest.TestCase):

    def test_normvel(self):
        self.assertEqual(0, Channels.normvel(0))
        self.assertEqual(0, Channels.normvel(1))
        self.assertEqual(.5, Channels.normvel(0x40))
        self.assertEqual(1, Channels.normvel(0x7f))
