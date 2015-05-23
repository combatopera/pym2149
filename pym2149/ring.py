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

signaldtype = np.uint8 # Slightly faster than plain old int.
derivativedtype = np.int8 # Suitable for any signal in [0, 127].
floatdtype = np.float32 # Effectively about 24 bits.

class AbstractRing:

    def __init__(self, npbuf, loopstart):
        self.buf = npbuf
        self.limit = len(npbuf)
        self.loopstart = loopstart

class SimpleRing(AbstractRing):

    def __init__(self, dtype, g, introlen):
        AbstractRing.__init__(self, np.fromiter(g, dtype), introlen)

    def newcursor(self):
        c = RingCursor(self)
        c.putstrided = c.putstridedsimple
        return c

class DerivativeRing(AbstractRing):

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
        AbstractRing.__init__(self, np.fromiter(h(), derivativedtype), introlen + 1)

    def newcursor(self):
        c = RingCursor(self)
        c.putstrided = c.putstridedderivative
        c.putindexed = c.putindexedderivative
        return c

class RingCursor:

    def __init__(self, ring):
        self.index = 0
        self.ring = ring

    def putstridedderivative(self, target, start, step, ringn):
        contextdc = self.contextdc()
        self.putstridedsimple(target, start, step, ringn)
        target.addtofirst(contextdc) # Add last value of previous integral.

    def putstridedsimple(self, target, start, step, ringn):
        while ringn:
            n = min(self.ring.limit - self.index, ringn)
            end = start + step * n
            ringend = self.index + n
            target.putstrided(start, end, step, self.ring.buf[self.index:ringend])
            start = end
            self.index = self.ring.loopstart if ringend == self.ring.limit else ringend
            ringn -= n

    def putindexedderivative(self, target, indices):
        contextdc = self.contextdc()
        while indices.shape[0]:
            n = min(self.ring.limit - self.index, indices.shape[0])
            ringend = self.index + n
            target.putindexed(indices[:n], self.ring.buf[self.index:ringend])
            self.index = self.ring.loopstart if ringend == self.ring.limit else ringend
            indices = indices[n:]
        target.addtofirst(contextdc)

    def contextdc(self):
        # Observe this can break through loopstart, in which case value should be same as last:
        return self.ring.dc[self.index - 1] if self.index else 0
