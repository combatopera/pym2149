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
from pyrbo import turbo, T, U

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

self_buf = that_buf = py_indices = None

class Buf:

    index = np.uint32

    def __init__(self, buf):
        self.buf = buf

    def __len__(self):
        return len(self.buf)

    def last(self):
        return self.buf[-1]

    @turbo(self = dict(buf = [T]), endframe = index, that = dict(buf = [T]), i = index)
    def copyasprefix(self, endframe, that):
        for i in xrange(endframe):
            self_buf[i] = that_buf[i]

    @turbo(self = dict(buf = [T]), that = dict(buf = [T]), startframe = index, endframe = index, i = index)
    def copywindow(self, that, startframe, endframe):
        for i in xrange(endframe - startframe):
            self_buf[i] = that_buf[startframe]
            startframe += 1

    def fillpart(self, startframe, endframe, value):
        self.fillpartimpl(self.buf, startframe, endframe, self.buf.dtype.type(value))

    @turbo(self = {}, buf = [T], i = np.uint32, endframe = np.uint32, value = T)
    def fillpartimpl(self, buf, i, endframe, value):
        while i < endframe:
            buf[i] = value
            i += 1

    @turbo(self = dict(buf = [T]), startframe = index, endframe = index, thatnp = [T], j = index)
    def partcopyintonp(self, startframe, endframe, thatnp):
        for j in xrange(endframe - startframe):
            that_buf[j] = self_buf[startframe]
            startframe += 1

    def fill(self, value):
        self.fillimpl(self.buf, len(self.buf), self.buf.dtype.type(value))

    @turbo(self = {}, buf = [T], n = np.uint32, value = T)
    def fillimpl(self, buf, n, value):
        while n:
            n -= 1
            buf[n] = value

    @turbo(self = dict(buf = [T]), start = index, end = index, step = index, data = [T], j = index)
    def putstrided(self, start, end, step, data):
        j = 0
        while start < end:
            self_buf[start] = data[j]
            start += step
            j += 1

    @turbo(self = dict(buf = [T]), indices = [U], data = [T], i = index)
    def putindexed(self, indices, data):
        for i in xrange(py_indices.size):
            self_buf[indices[i]] = data[i]

    def addtofirst(self, val):
        self.buf[0] += val

    def integrate(self, that):
        np.cumsum(that.buf, out = self.buf)

    def ceildiv(self, divisor, alreadynegated = False):
        if not alreadynegated:
            self.buf *= -1
        self.buf //= divisor
        self.buf *= -1

    def mulbuf(self, that):
        self.buf *= that.buf

    def mapbuf(self, that, lookup):
        self.mapbufimpl(self.buf, that.buf, lookup, len(that))

    @turbo(self = {}, buf = [T], that = [U], lookup = [T], n = np.uint32)
    def mapbufimpl(self, buf, that, lookup, n):
        while n:
            n -= 1
            buf[n] = lookup[that[n]]

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
