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
        self.impl = SpeedDetector(10, self.callback)

    def d(self, c):
        self.impl(0 if c == '.' else ord(c) - ord('0'))

    def play(self, eventcounts):
        #print eventcounts
        for ec in eventcounts:
            self.d(ec)

    def callback(self, _, speed):
        self.speeds.append(speed)

    def test_works(self):
        self.play('1..1..1')
        self.assertEqual([3], self.speeds)

    def test_works2(self):
        self.play('1..1..1..1..1..1..1')
        self.assertEqual([3], self.speeds)

    def test_increase(self):
        self.play('1..1..1...1...1')
        self.assertEqual([3, 4], self.speeds)

    def test_decrease(self):
        self.play('1...1...1..1..1')
        self.assertEqual([4, 3], self.speeds)

    def test_multiply(self):
        self.play('1..1..1.....1.....1')
        self.assertEqual([3, 6], self.speeds)

    def test_divide(self):
        self.play('1.....1.....1..1..1')
        self.assertEqual([6, 3], self.speeds)

    def test_temporarydivide(self):
        self.play('5.....5.....5..2..5.....5.....5')
        self.assertEqual([6], self.speeds)

    def test_gracenotes(self):
        self.play('5.....5.....5....25.....5.....5')
        self.assertEqual([6], self.speeds)

if '__main__' == __name__:
    unittest.main()
