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

  def add(self, value):
    self.buf += value

  def addbuf(self, that):
    self.buf += that.buf

  def orbuf(self, that):
    self.buf |= that.buf

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
