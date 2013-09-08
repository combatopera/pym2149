class Buf:

  def __init__(self):
    self.buf = []

  def atleast(self, size):
    if len(self.buf) < size:
      # I think to extend we'd need yet another sequence, so new list is good:
      self.buf = [None] * size
    return self.buf

  def __getitem__(self, key):
    return self.buf[key]
