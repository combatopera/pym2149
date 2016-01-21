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

import numpy as np
from util import singleton
from pyrbo import turbo, T

@singleton
class nullbuf:

    def last(self, *args): pass

    def copyasprefix(self, *args): pass

    def copywindow(self, *args): pass

    def fillpart(self, *args): pass

    def partcopyintonp(self, *args): pass

    def fill(self, *args): pass

    def putstrided(self, *args): pass

    def putindexed(self, *args): pass

    def addtofirst(self, *args): pass

    def integrate(self, *args): pass

    def subbuf(self, *args): pass

class Buf:

    def __init__(self, buf):
        self.buf = buf

    def __len__(self):
        return len(self.buf)

    def last(self):
        return self.buf[-1]

    def copyasprefix(self, endframe, that):
        self.buf[:endframe] = that.buf

    def copywindow(self, that, startframe, endframe):
        self.buf[:] = that.buf[startframe:endframe]

    def fillpart(self, startframe, endframe, value):
        self.buf[startframe:endframe] = value

    def partcopyintonp(self, startframe, endframe, thatnp):
        thatnp[:] = self.buf[startframe:endframe]

    def fill(self, value):
        self.buf[:] = value

    def putstrided(self, start, end, step, data):
        self.putstridedimpl(T = self.buf.dtype)(self.buf, start, end, step, data)

    @turbo(buf = [T], i = np.uint32, end = np.uint32, step = np.uint32, data = [T], j = np.uint32)
    def putstridedimpl(buf, i, end, step, data):
        j = 0
        while i < end:
            buf[i] = data[j]
            i += step
            j += 1

    def putindexed(self, indices, data):
        self.buf[indices] = data

    def addtofirst(self, val):
        self.buf[0] += val

    def integrate(self, that):
        np.cumsum(that.buf, out = self.buf)

    def ceildiv(self, divisor, alreadynegated = False):
        if not alreadynegated:
            self.buf *= -1
        self.buf //= divisor
        self.buf *= -1

    def arange(self, scale):
        self.buf[0] = 0
        self.buf[1:] = scale
        np.cumsum(self.buf, out = self.buf)

    def mulbuf(self, that):
        self.buf *= that.buf

    def mapbuf(self, that, lookup):
        lookup.take(that.buf, out = self.buf)

    def add(self, value):
        self.buf += value

    def mul(self, value):
        self.buf *= value

    def subbuf(self, that):
        self.buf -= that.buf

    def andbuf(self, that):
        self.buf &= that.buf

    def copybuf(self, that):
        self.buf[:] = that.buf

    def tofile(self, fileobj):
        self.buf.tofile(fileobj)

    def differentiate(self, lastofprev, that):
        self.copybuf(that)
        self.buf[0] -= lastofprev
        self.buf[1:] -= that.buf[:-1]

    def tolist(self): # For tests.
        return list(self.buf)

class MasterBuf:

    def __init__(self, dtype):
        self.dtype = dtype
        self.setsize(0)

    def setsize(self, size):
        self.buf = np.empty(size, self.dtype)
        self.bufobj = Buf(self.buf)
        self.size = size

    def ensureandcrop(self, framecount):
        if self.size > framecount:
            return Buf(self.buf[:framecount])
        if self.size < framecount:
            # Ideally we would resize in-place, but that can fall foul of numpy reference counting:
            self.setsize(framecount)
        return self.bufobj
