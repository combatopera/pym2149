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
from pyrbo import turbo, LOCAL
from const import u4

class ToneOsc(BufNode):

    def __init__(self, scale, periodreg):
        BufNode.__init__(self, signaldtype)
        self.value = 1
        self.progress = 0
        self.scale = scale
        self.periodreg = periodreg

    def callimpl(self):
        self.value, self.progress = self.toneimpl()

    @turbo(self = dict(blockbuf = dict(buf = [signaldtype]), block = dict(framecount = u4), value = signaldtype, progress = u4, scale = u4, periodreg = dict(value = u4)), stepsize = u4, i = u4, j = u4, n = u4)
    def toneimpl(self):
        self_blockbuf_buf = self_block_framecount = self_value = self_progress = self_scale = self_periodreg_value = LOCAL
        stepsize = self_periodreg_value * self_scale
        i = 0
        if self_progress < stepsize:
            j = min(stepsize - self_progress, self_block_framecount)
            while i < j:
                self_blockbuf_buf[i] = self_value
                i += 1
        if i == self_block_framecount:
            self_progress += self_block_framecount
        else:
            self_value = 1 - self_value
            n = (self_block_framecount - i) // stepsize
            while n:
                j = i + stepsize
                while i < j:
                    self_blockbuf_buf[i] = self_value
                    i += 1
                self_value = 1 - self_value
                n -= 1
            self_progress = self_block_framecount - i
            while i < self_block_framecount:
                self_blockbuf_buf[i] = self_value
                i += 1
        return self_value, self_progress

class NoiseOsc(BufNode):

    def __init__(self, scale, periodreg, noiseshape):
        BufNode.__init__(self, signaldtype)
        self.scale = scale
        self.periodreg = periodreg
        self.noiseshape = noiseshape

    def callimpl(self):
        self.noiseimpl()

    @turbo(self = dict())
    def noiseimpl(self):
        pass
