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

from .shapes import makesample5shape
from unittest import TestCase

class TestMakeSample5Shape(TestCase):

    def test_happypath(self):
        s = makesample5shape([0x00, 0x7f, 0x80, 0xff], False, False)
        self.assertEqual(4, s.size)
        self.assertEqual(3, s.introlen)
        self.assertEqual([1, 27, 27, 31], list(s.buf))

    def test_signed(self):
        s = makesample5shape([0x80, 0xff, 0x00, 0x7f], True, False)
        self.assertEqual(4, s.size)
        self.assertEqual(3, s.introlen)
        self.assertEqual([1, 27, 27, 31], list(s.buf))

    def test_usebestresolution(self):
        for data in [0x00, 0x11, 0x22, 0x33], [0xcc, 0xdd, 0xee, 0xff]:
            s = makesample5shape(data, False, False)
            self.assertEqual(4, s.size)
            self.assertEqual(3, s.introlen)
            self.assertEqual([1, 15, 19, 21], list(s.buf))

    def test_is4bit(self):
        for signed in False, True:
            s = makesample5shape([0, 1, 2, 3, 4], signed, True)
            self.assertEqual(5, s.size)
            self.assertEqual(4, s.introlen)
            self.assertEqual([1, 3, 5, 7, 9], list(s.buf))
