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

from .lha import Stream, Tree
from unittest import TestCase

class TestTree(TestCase):

    def test_canonical(self):
        tree = Tree.canonical([2, 3, 0, 0, 0, 0, 7, 6, 5, 4, 3, 3, 3, 3, 7])
        self.assertEqual({
            0b100: 0,
            0b1010: 1,
            0b1011: 10,
            0b1100: 11,
            0b1101: 12,
            0b1110: 13,
            0b11110: 9,
            0b111110: 8,
            0b1111110: 7,
            0b11111110: 6,
            0b11111111: 14,
        }, tree.lookup)
        s = Stream(b'\xfe\x6e') # 11111110 01101110
        self.assertEqual(14, tree.readvalue(s))
        self.assertEqual(0, tree.readvalue(s))
        self.assertEqual(13, tree.readvalue(s))
        self.assertEqual(9, tree.readvalue(s))
        self.assertEqual(2, s.cursor)
        self.assertEqual(8, s.remaining)

    def test_degenerate(self):
        tree = Tree.degenerate(100)
        self.assertEqual({1: 100}, tree.lookup)
        s = Stream(b'')
        self.assertEqual(100, tree.readvalue(s))
        self.assertEqual(100, tree.readvalue(s))
        self.assertEqual(0, s.cursor)
        self.assertEqual(8, s.remaining)
