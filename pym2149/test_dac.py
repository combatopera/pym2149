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

from .buf import BufType
from .dac import Dac
from .nod import Block, BufNode
from unittest import TestCase

class Ramps(BufNode):

    buftype = BufType.signal

    def __init__(self):
        super().__init__(self.buftype)

    def callimpl(self):
        for i in range(self.block.framecount):
            self.blockbuf.fillpart(i, i + 1, self.buftype.dtype(i))

class TestDac(TestCase):

    def test_works(self):
        d = Dac(Ramps(), 16, 1)
        self.assertEqual([d.leveltopeaktopeak[v] for v in range(32)], d.call(Block(32)).tolist())
