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

from .const import u4
from .shapes import floatdtype, signaldtype
from diapyr.util import enum
from pyrbo import generic, LOCAL, turbo, T
import numpy as np

@enum(
    ['float', floatdtype],
    ['int16', np.int16],
    ['short', np.short],
    ['signal', signaldtype],
)
class BufType:

    def __init__(self, _, dtype):
        self.dtype = dtype

    def __call__(self):
        return MasterBuf(self.dtype)

groupsets = {T: [{t.dtype for t in BufType.enum}]}

class Buf(metaclass = generic):

    def _turbo(**types):
        return turbo(types = dict(self = dict(buf = [T]), **types), groupsets = groupsets)

    def __init__(self, buf):
        self.buf = buf

    def __len__(self):
        return len(self.buf)

    def last(self):
        return self.buf[-1]

    @_turbo(endframe = u4, that = dict(buf = [T]), i = u4)
    def copyasprefix(self, endframe, that):
        self_buf = that_buf = LOCAL
        for i in range(endframe):
            self_buf[i] = that_buf[i]

    @_turbo(that = dict(buf = [T]), startframe = u4, endframe = u4, i = u4)
    def copywindow(self, that, startframe, endframe):
        self_buf = that_buf = LOCAL
        for i in range(endframe - startframe):
            self_buf[i] = that_buf[startframe]
            startframe += 1

    @_turbo(startframe = u4, endframe = u4, value = T)
    def fillpart(self, startframe, endframe, value):
        self_buf = LOCAL
        while startframe < endframe:
            self_buf[startframe] = value
            startframe += 1

    @_turbo(startframe = u4, endframe = u4, thatnp = [T], j = u4)
    def partcopyintonp(self, startframe, endframe, thatnp):
        self_buf = LOCAL
        for j in range(endframe - startframe):
            thatnp[j] = self_buf[startframe]
            startframe += 1

    @_turbo(value = np.int8, i = u4, v = T)
    def fill_i1(self, value):
        self_buf = py_self_buf = LOCAL
        v = value # Cast once.
        for i in range(py_self_buf.size):
            self_buf[i] = v

    @_turbo(value = T, i = u4)
    def fill_same(self, value):
        self_buf = py_self_buf = LOCAL
        for i in range(py_self_buf.size):
            self_buf[i] = value

    @_turbo(start = u4, end = u4, step = u4, data = [T], j = u4)
    def putstrided(self, start, end, step, data):
        self_buf = LOCAL
        j = 0
        while start < end:
            self_buf[start] = data[j]
            start += step
            j += 1

    def ceildiv(self, divisor, alreadynegated = False):
        if not alreadynegated:
            self.buf *= -1
        self.buf //= divisor
        self.buf *= -1

    def mulbuf(self, that):
        self.buf *= that.buf

    @_turbo(that = dict(buf = [signaldtype]), lookup = [T], i = u4)
    def mapbuf(self, that, lookup):
        self_buf = that_buf = py_that_buf = LOCAL
        for i in range(py_that_buf.size):
            self_buf[i] = lookup[that_buf[i]]

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
        # TODO LATER: Reinstate tofile when fixed upstream, see https://github.com/numpy/numpy/issues/7380 for details.
        fileobj.write(self.buf.tobytes())

    def differentiate(self, lastofprev, that):
        self.copybuf(that)
        self.buf[0] -= lastofprev
        self.buf[1:] -= that.buf[:-1]

    def tolist(self): # For tests.
        return list(self.buf)

class MasterBuf:

    def __init__(self, dtype):
        self.bufcls = Buf[T, dtype]
        self.dtype = dtype
        self.setsize(0)

    def setsize(self, size):
        self.buf = np.empty(size, self.dtype)
        self.bufobj = self.bufcls(self.buf)
        self.size = size

    def ensureandcrop(self, framecount):
        if self.size > framecount:
            return self.bufcls(self.buf[:framecount])
        if self.size < framecount:
            # Ideally we would resize in-place, but that can fall foul of numpy reference counting:
            self.setsize(framecount)
        return self.bufobj
