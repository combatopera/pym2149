import numpy as np

class Buf:

  def __init__(self, buf):
    self.buf = buf

  def framecount(self):
    return self.buf.shape[0]

  def fill(self, startframe, endframe, value):
    self.buf[startframe:endframe] = value

  def scale(self, factor):
    self.buf *= factor

  def add(self, value):
    self.buf += value

  def addbuf(self, that):
    self.buf += that.buf

  def copybuf(self, that):
    self.buf[:] = that.buf

  def tofile(self, fileobj):
    self.buf.tofile(fileobj)

  def ensureandcrop(self, framecount):
    thisframecount = self.framecount()
    if thisframecount == framecount:
      return self
    if thisframecount < framecount:
      self.buf.resize(framecount)
      return self
    return Buf(self.buf[:framecount])

class MasterBuf(Buf):

  def __init__(self, framecount, dtype):
    Buf.__init__(self, np.empty(framecount, dtype))
