class Buf:

  def __init__(self):
    self.buf = []

  def atleast(self, n):
    if len(self.buf) < n:
      self.buf = [None] * n
    return self.buf

  def __getitem__(self, key):
    return self.buf[key]
