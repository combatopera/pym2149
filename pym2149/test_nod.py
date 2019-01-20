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
from .nod import Node, Block

class MyNode(Node):

    def __init__(self):
        super().__init__()
        self.x = 0

    def callimpl(self):
        x = self.block.framecount + self.x
        self.x += 1
        return x

class TestNode(unittest.TestCase):

    def test_works(self):
        n = MyNode()
        b1 = Block(10)
        b2 = Block(20)
        for _ in range(2):
            self.assertEqual(10, n.call(b1))
        for _ in range(2):
            self.assertEqual(21, n.call(b2))
        for _ in range(2):
            self.assertEqual(12, n.call(b1))
