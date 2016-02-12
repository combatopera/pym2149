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

import numpy as np, itertools
from util import ceildiv
from pyrbo import turbo, LOCAL
from const import u4

signaldtype = np.uint8 # Slightly faster than plain old int.
derivativedtype = np.int8 # Suitable for any signal in [0, 127].
floatdtype = np.float32 # Effectively about 24 bits.

class DerivativeRing:

    minloopsize = 1000

    def __init__(self, g, introlen = 0):
        self.dc = list(g)
        mindc = min(self.dc)
        maxdc = max(self.dc)
        if mindc < 0 or maxdc > 255:
            raise Exception("%s not wide enough for: [%s, %s]" % (signaldtype.__name__, mindc, maxdc))
        self.dc.append(self.dc[introlen]) # Necessary as the 2 jumps to this value needn't be equal.
        self.loopstart = introlen + 1
        unitlen = len(self.dc) - self.loopstart
        self.dc.extend(itertools.chain(*itertools.tee(itertools.islice(self.dc, self.loopstart, self.loopstart + unitlen), ceildiv(self.minloopsize - unitlen, unitlen))))
        self.limit = len(self.dc)
        def h():
            yield self.dc[0]
            for i in xrange(1, self.limit):
                yield self.dc[i] - self.dc[i - 1]
        mindiff = min(h())
        maxdiff = max(h())
        if mindiff < -128 or maxdiff > 127:
            raise Exception("%s not wide enough for: [%s, %s]" % (derivativedtype.__name__, mindiff, maxdiff))
        self.npbuf = np.fromiter(h(), derivativedtype)

    def tolist(self): # For tests.
        return list(self.npbuf)

    def newcursor(self):
        return RingCursor(self)

class RingCursor:

    def __init__(self, ring):
        self.index = 0
        self.ring = ring

    def swapring(self, ring):
        if ring.limit != self.ring.limit:
            raise Exception("Expected limit %s but was: %s" % (self.ring.limit, ring.limit))
        self.ring = ring

    @turbo(self = dict(index = u4, ring = dict(npbuf = [derivativedtype], limit = u4, loopstart = u4)), target = dict(buf = [derivativedtype]), start = u4, step = u4, ringn = u4, i = u4, contextdc = derivativedtype, end = u4, ringend = u4, n = u4)
    def putstrided(self, target, start, step, ringn):
        py_target_buf = target_buf = self_ring_limit = self_index = self_ring_npbuf = self_ring_loopstart = LOCAL
        for i in xrange(py_target_buf.size):
            target_buf[i] = 0
        contextdc = self.contextdc()
        while ringn:
            n = min(self_ring_limit - self_index, ringn)
            end = start + step * n
            ringend = self_index + n
            while start < end:
                target_buf[start] = self_ring_npbuf[self_index]
                start += step
                self_index += 1
            self_index = self_ring_loopstart if ringend == self_ring_limit else ringend
            ringn -= n
        target_buf[0] += contextdc # Add last value of previous integral.
        self.index = self_index

    @turbo(self = dict(index = u4, ring = dict(npbuf = [derivativedtype], limit = u4, loopstart = u4)), target = dict(buf = [derivativedtype]), indices = [np.int64], ifrom = u4, ringn = u4, contextdc = derivativedtype, n = u4, ito = u4, ringend = u4, i = u4)
    def putindexed(self, target, indices):
        py_indices = target_buf = py_target_buf = self_ring_loopstart = self_ring_limit = self_ring_npbuf = self_index = LOCAL
        ifrom = 0
        ringn = py_indices.size
        for i in xrange(py_target_buf.size):
            target_buf[i] = 0
        contextdc = self.contextdc()
        while ringn:
            n = min(self_ring_limit - self_index, ringn)
            ito = ifrom + n
            ringend = self_index + n
            for i in xrange(n):
                target_buf[indices[ifrom + i]] = self_ring_npbuf[self_index + i]
            ifrom = ito
            self_index = self_ring_loopstart if ringend == self_ring_limit else ringend
            ringn -= n
        target_buf[0] += contextdc
        self.index = self_index

    def contextdc(self):
        # Observe this can break through loopstart, in which case value should be same as last:
        return self.ring.dc[self.index - 1] if self.index else 0
