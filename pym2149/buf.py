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

class AnyBuf:

  @staticmethod
  def putringops(ring, ringstart, ringn, ringloop = 0):
    ringsize = ring.shape[0]
    ops = 0
    while ringn:
      n = min(ringsize - ringstart, ringn)
      ops += 1
      if ringstart + n == ringsize:
        ringstart = ringloop
      ringn -= n
    return ops

@singleton
class NullBuf(AnyBuf):

  def fillpart(self, *args): pass

  def fill(self, *args): pass

  def putring(self, *args): pass

  def subbuf(self, *args): pass

  def putstrided(self, *args): pass

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

  def putstrided(self, off, step, val):
    self.buf[off::step] = val

  def addtofirst(self, val):
    self.buf[0] += val

  def integrate(self, that):
    np.cumsum(that.buf, out = self.buf)

  def mulbuf(self, that):
    self.buf *= that.buf

  def mapbuf(self, that, lookup):
    lookup.take(that.buf, out = self.buf)

  def putring(self, start, step, ring, ringstart, ringn, ringloop = 0):
    ringsize = ring.shape[0]
    while ringn:
      n = min(ringsize - ringstart, ringn)
      end = start + step * n
      ringend = ringstart + n
      self.buf[start:end:step] = ring[ringstart:ringend]
      start = end
      if ringend == ringsize:
        ringstart = ringloop
      ringn -= n

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

  def nonzeros(self):
    return np.flatnonzero(self.buf) # XXX: Can we avoid making a new array?

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
