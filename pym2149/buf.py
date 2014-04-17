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

def singleton(f):
  return f()

class Ring:

  def __init__(self, dtype, g, loopstart):
    self.buf = np.fromiter(g, dtype)
    self.loopstart = loopstart

  def __len__(self):
    return len(self.buf)

class DiffRing(Ring): # TODO: Inline 0 initial dc, always add one element.

  def __init__(self, g, dc, dtype, prolog = 0):
    self.dc = list(g)
    jump = self.dc[-1] != (dc, self.dc[prolog - 1])[bool(prolog)]
    if jump:
      self.dc.append(self.dc[prolog])
    def h():
      yield self.dc[0] - dc
      for i in xrange(1, len(self.dc)):
        yield self.dc[i] - self.dc[i - 1]
    Ring.__init__(self, dtype, h(), prolog + jump)
    self.initialdc = dc

class AnyBuf:

  @staticmethod
  def putringops(ring, ringcursor, ringn):
    limit = len(ring)
    ops = 0
    while ringn:
      n = min(limit - ringcursor, ringn)
      ops += 1
      if ringcursor + n == limit:
        ringcursor = ring.loopstart
      ringn -= n
    return ops

class RingCursor:

  def __init__(self, ring):
    self.limit = len(ring)
    self.index = 0
    self.ring = ring

  def put(self, target, start, step, ringn):
    while ringn:
      n = min(self.limit - self.index, ringn)
      end = start + step * n
      ringend = self.index + n
      target.putstrided(start, end, step, self.ring.buf[self.index:ringend])
      start = end
      if ringend == self.limit:
        # Allow non-rings to use one iteration of this method:
        try:
          self.index = self.ring.loopstart
        except AttributeError:
          self.index = None
      else:
        self.index = ringend
      ringn -= n

  def put2(self, target, indices):
    while indices.shape[0]:
      n = min(self.limit - self.index, indices.shape[0])
      ringend = self.index + n
      target.putindexed(indices[:n], self.ring.buf[self.index:ringend])
      if ringend == self.limit:
        self.index = self.ring.loopstart
      else:
        self.index = ringend
      indices = indices[n:]

  def currentdc(self):
    # Observe this can break through loopstart, in which case value should be same as last:
    return (self.ring.initialdc, self.ring.dc[self.index - 1])[bool(self.index)]

@singleton
class NullBuf(AnyBuf):

  def fillpart(self, *args): pass

  def fill(self, *args): pass

  def subbuf(self, *args): pass

  def putstrided(self, *args): pass

  def putindexed(self, *args): pass

  def addtofirst(self, *args): pass

  def integrate(self, *args): pass

class Buf(AnyBuf):

  def __init__(self, buf):
    self.buf = buf

  def __len__(self):
    return len(self.buf)

  def fillpart(self, startframe, endframe, value):
    self.buf[startframe:endframe] = value

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
    diff = self.ensureandcrop(len(that))
    diff.copybuf(that)
    diff.buf[0] -= lastofprev
    diff.buf[1:] -= that.buf[:-1]
    return diff

  def ensureandcrop(self, framecount):
    thisframecount = self.buf.shape[0]
    if thisframecount == framecount:
      return self
    if thisframecount < framecount:
      self.buf.resize(framecount)
      return self
    return Buf(self.buf[:framecount])

  def tolist(self): # For tests.
    return list(self.buf)

class MasterBuf(Buf):

  def __init__(self, dtype):
    Buf.__init__(self, np.empty(0, dtype))
