import numpy as np

class Buf:

  def __init__(self, buf):
    self.buf = buf

  def framecount(self):
    return self.buf.shape[0]

  def __setitem__(self, key, value):
    self.buf[key] = value

  def __getitem__(self, key):
    return self.buf[key]

  def fill(self, startframe, endframe, value):
    self.buf[startframe:endframe] = value

  def scale(self, factor):
    self.buf *= factor

  def xform(self, value):
    self.buf += value

  def add(self, that):
    self.buf += that.buf

  def tofile(self, fileobj):
    self.buf.tofile(fileobj)

  def crop(self, framecount):
    thisframecount = self.framecount()
    if thisframecount == framecount:
      return self
    if thisframecount < framecount:
      self.buf.resize(framecount)
      return self
    return Buf(self.buf[:framecount])

class SimpleBuf(Buf):

  def __init__(self, framecount):
    Buf.__init__(self, np.empty(framecount))
