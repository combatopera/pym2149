import numpy as np

class Buf:

  def __init__(self):
    self.buf = np.empty(0)

  def __len__(self):
    return self.buf.shape[0]

  def atleast(self, size):
    if len(self) < size:
      self.buf.resize(size)
    return self

  def __setitem__(self, key, value):
    self.buf[key] = value

  def __getitem__(self, key):
    return self.buf[key]

  def fill(self, start, end, value):
    self.buf[start:end] = value

  def scale(self, start, end, factor):
    self.buf[start:end] *= factor
