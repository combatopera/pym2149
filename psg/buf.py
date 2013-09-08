import numpy as np

class Buf:

  def __init__(self, buf):
    self.buf = buf

  def __len__(self):
    return self.buf.shape[0]

  def __setitem__(self, key, value):
    self.buf[key] = value

  def __getitem__(self, key):
    return self.buf[key]

  def fill(self, start, end, value):
    self.buf[start:end] = value

  def scale(self, start, end, factor):
    self.buf[start:end] *= factor

class SimpleBuf(Buf):

  def __init__(self):
    Buf.__init__(self, np.empty(0))

  def atleast(self, size):
    if len(self) < size:
      self.buf.resize(size)
    return self

class RingBuf(Buf):

  def __init__(self, size):
    Buf.__init__(self, np.zeros(size))

  def atleast(self, size):
    keep = len(self) - size
    if keep >= 0:
      self.buf[:keep] = self.buf[-keep:]
      return Buf(self.buf[keep:])

  def convolve(self, taps):
    return np.convolve(self.buf, taps, mode = 'valid')[0]
