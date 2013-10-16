import numpy as np

class Buf:

  def __init__(self, buf):
    self.buf = buf

  def fillpart(self, startframe, endframe, value):
    self.buf[startframe:endframe] = value

  def fill(self, value):
    self.buf[:] = value

  def mulbuf(self, that):
    self.buf *= that.buf

  def mapbuf(self, that, lookup):
    lookup.take(that.buf, out = self.buf)

  def putring(self, start, step, ring, ringstart, ringn):
    ringsize = ring.shape[0]
    while ringn:
      n = min(ringsize - ringstart, ringn)
      end = start + step * n
      ringend = ringstart + n
      self.buf[start:end:step] = ring[ringstart:ringend]
      start = end
      ringstart = ringend % ringsize
      ringn -= n

  def add(self, value):
    self.buf += value

  def subbuf(self, that):
    self.buf -= that.buf

  def andbuf(self, that):
    self.buf &= that.buf

  def copybuf(self, that):
    self.buf[:] = that.buf

  def tofile(self, fileobj):
    self.buf.tofile(fileobj)

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
