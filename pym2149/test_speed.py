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
from speed import SpeedDetector

class TestSpeedDetector(unittest.TestCase):

    def setUp(self):
        self.speeds = []
        self.d = SpeedDetector(self.callback)

    def callback(self, _, speed):
        self.speeds.append(speed)

    def test_works(self):
        for ec in 1, 0, 0, 1:
            self.d(ec)
        self.assertEqual([3], self.speeds)

    def test_increase(self):
        for ec in 1, 0, 0, 1, 0, 0, 0, 1:
            self.d(ec)
        self.assertEqual([3, 4], self.speeds)

    def test_decrease(self):
        for ec in 1, 0, 0, 0, 1, 0, 0, 1:
            self.d(ec)
        self.assertEqual([4, 3], self.speeds)

    def test_multiply(self):
        for ec in 1, 0, 0, 1, 0, 0, 0, 0, 0, 1:
            self.d(ec)
        self.assertEqual([3, 6], self.speeds)

    def test_divide(self):
        for ec in 1, 0, 0, 0, 0, 0, 1, 0, 0, 1:
            self.d(ec)
        self.assertEqual([6, 3], self.speeds)

    def test_temporarydivide(self):
        for ec in 5, 0, 0, 0, 0, 0, 5, 0, 0, 2, 0, 0, 5, 0, 0, 0, 0, 0, 5:
            self.d(ec)
        self.assertEqual([6], self.speeds)

    def test_gracenotes(self):
        for ec in 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 2, 5, 0, 0, 0, 0, 0, 5:
            self.d(ec)
        self.assertEqual([6], self.speeds)

if '__main__' == __name__:
    unittest.main()
