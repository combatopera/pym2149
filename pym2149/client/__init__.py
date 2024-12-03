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

class BufferFiller:

    def __init__(self, portcount, buffersize, init, flip):
        self.portcount = portcount
        self.buffersize = buffersize
        self._newbuf(init)
        self.flip = flip

    def __call__(self, outbufs):
        n = len(outbufs[0])
        i = 0
        while i < n:
            m = min(n - i, self.buffersize - self.cursor)
            for portindex in range(self.portcount):
                self.outbuf[portindex, self.cursor:self.cursor + m] = outbufs[portindex].buf[i:i + m]
            self.cursor += m
            i += m
            if self.cursor == self.buffersize:
                self._newbuf(self.flip)

    def _newbuf(self, factory):
        outbuf = factory().view()
        outbuf.shape = self.portcount, self.buffersize
        self.outbuf = outbuf
        self.cursor = 0
