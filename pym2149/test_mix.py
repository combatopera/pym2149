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

import unittest, numpy as np
from .mix import IdealMixer, Multiplexer
from .nod import BufNode, Block, Container
from .out import TrivialOutChannel

class Counter(BufNode):

    dtype = np.int64 # Closest thing to int.

    def __init__(self, x = 0):
        super().__init__(self.dtype)
        self.x = self.dtype(x)

    def callimpl(self):
        for frameindex in range(self.block.framecount):
            self.blockbuf.fillpart(frameindex, frameindex + 1, self.x)
            self.x += 1

class TestIdealMixer(unittest.TestCase):

    def expect(self, m, values, actual):
        self.assertEqual(len(values), len(actual))
        for i in range(len(values)):
            self.assertAlmostEqual(m.datum - values[i], actual.buf[i])

    def test_works(self):
        c = Container([Counter(10), Counter()])
        m = IdealMixer(c, 16, TrivialOutChannel)
        self.expect(m, [10, 12, 14, 16, 18], m.call(Block(5)))
        # Check the buffer is actually cleared first:
        self.expect(m, [20, 22, 24, 26, 28], m.call(Block(5)))

class TestMultiplexer(unittest.TestCase):

    def test_works(self):
        a = Counter()
        b = Counter(10)
        c = Counter(30)
        m = Multiplexer(Counter.dtype, [a, b, c])
        self.assertEqual([0, 10, 30, 1, 11, 31, 2, 12, 32, 3, 13, 33, 4, 14, 34], m.call(Block(5)).tolist())
