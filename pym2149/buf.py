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

signaldtype = np.uint8 # Slightly faster than plain old int.
derivativedtype = np.int8 # Suitable for any signal in [0, 127].
floatdtype = np.float32 # Effectively about 24 bits.

class AbstractRing:

    def __init__(self, npbuf):
        self.buf = npbuf
        self.limit = len(npbuf)

class Ring(AbstractRing):

    def __init__(self, dtype, g, loopstart):
        AbstractRing.__init__(self, np.fromiter(g, dtype))
        self.loopstart = loopstart

class OnceRing(AbstractRing):

    def __init__(self, buf):
        AbstractRing.__init__(self, buf.buf)

class DerivativeRing(Ring):

    def __init__(self, g, introlen = 0):
        self.dc = list(g)
        mindc = min(self.dc)
        maxdc = max(self.dc)
        if mindc < 0 or maxdc > 255:
            raise Exception("%s not wide enough for: [%s, %s]" % (self.signaldtype.__name__, mindc, maxdc))
        self.dc.append(self.dc[introlen])
        def h():
            yield self.dc[0]
            for i in xrange(1, len(self.dc)):
                yield self.dc[i] - self.dc[i - 1]
        mindiff = min(h())
        maxdiff = max(h())
        if mindiff < -128 or maxdiff > 127:
            raise Exception("%s not wide enough for: [%s, %s]" % (self.derivativedtype.__name__, mindiff, maxdiff))
        Ring.__init__(self, derivativedtype, h(), introlen + 1)

class AnyBuf:

    @staticmethod
    def putringops(ring, ringcursor, ringn):
        ops = 0
        while ringn:
            n = min(ring.limit - ringcursor, ringn)
            ops += 1
            if ringcursor + n == ring.limit:
                ringcursor = ring.loopstart
            ringn -= n
        return ops

class RingCursor:

    def __init__(self, ring):
        self.index = 0
        self.ring = ring

    def putstrided(self, target, start, step, ringn):
        while ringn:
            n = min(self.ring.limit - self.index, ringn)
            end = start + step * n
            ringend = self.index + n
            target.putstrided(start, end, step, self.ring.buf[self.index:ringend])
            start = end
            if ringend == self.ring.limit:
                # Allow OnceRing to use one iteration of this method:
                try:
                    self.index = self.ring.loopstart
                except AttributeError:
                    self.index = None
            else:
                self.index = ringend
            ringn -= n

    def putindexed(self, target, indices):
        dcadjust = self.currentdc()
        while indices.shape[0]:
            n = min(self.ring.limit - self.index, indices.shape[0])
            ringend = self.index + n
            target.putindexed(indices[:n], self.ring.buf[self.index:ringend])
            if ringend == self.ring.limit:
                self.index = self.ring.loopstart
            else:
                self.index = ringend
            indices = indices[n:]
        target.addtofirst(dcadjust)

    def currentdc(self):
        # Observe this can break through loopstart, in which case value should be same as last:
        return self.ring.dc[self.index - 1] if self.index else 0

@singleton
class NullBuf(AnyBuf):

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

class Buf(AnyBuf):

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
        self.buf[start:end:step] = data

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
