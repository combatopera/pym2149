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

from nod import BufNode
from ring import signaldtype
from pyrbo import turbo
from const import u4
import numpy as np

class ToneOsc(BufNode):

    def __init__(self, scale, periodreg):
        BufNode.__init__(self, signaldtype)
        self.scale = scale
        self.periodreg = periodreg

    @turbo(self = dict(blockbuf = dict(buf = [signaldtype]), block = dict(framecount = u4), periodreg = dict(value = u4)), countdown = u4, value = signaldtype, i = u4)
    def callimpl(self):
        countdown = self_periodreg_value * 8
        value = 1
        for i in xrange(self_block_framecount):
            self_blockbuf_buf[i] = value
            countdown -= 1
            if not countdown:
                countdown = self_periodreg_value * 8
                value = 1 - value
