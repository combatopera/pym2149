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
from .speed import SpeedDetector

class TestSpeedDetector(unittest.TestCase):

    def check(self, expected, eventcounts):
        speeds = []
        detector = SpeedDetector(10, lambda _, speedphase, clarity: speeds.append(speedphase))
        for eventcount in eventcounts:
            detector(0 if eventcount == '.' else ord(eventcount) - ord('0'))
        self.assertEqual(expected, speeds)

    def test_works(self):
        self.check([(3, 0)], '1..1..1')
        self.check([(3, 1)], '.1..1..1')
        self.check([(3, 2)], '..1..1..1')
        self.check([(3, 0)], '1..1..1..1..1..1..1')
        self.check([(3, 1)], '.1..1..1..1..1..1..1')
        self.check([(3, 2)], '..1..1..1..1..1..1..1')

    def test_increase(self):
        self.check([(3, 0), (4, 2)], '1..1..1...1...1')

    def test_decrease(self):
        self.check([(4, 0), (3, 2)], '1...1...1..1..1')

    def test_multiply(self):
        self.check([(3, 0), (6, 0)], '1..1..1.....1.....1')
        self.check([(3, 1), (6, 1)], '.1..1..1.....1.....1')
        self.check([(3, 2), (6, 2)], '..1..1..1.....1.....1')

    def test_divide(self):
        self.check([(6, 0), (3, 0)], '1.....1.....1..1..1')
        self.check([(6, 1), (3, 1)], '.1.....1.....1..1..1')
        self.check([(6, 2), (3, 2)], '..1.....1.....1..1..1')

    def test_temporarydivide(self):
        self.check([(6, 0)], '5.....5.....5..2..5.....5.....5')

    def test_gracenotes(self):
        self.check([(6, 0)], '5.....5.....5....25.....5.....5')

    def test_sparse(self):
        self.check([(3, 0), (9, 3), (3, 0)], '1..1.....1..1........1.....1..1..1')
