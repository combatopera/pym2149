class Buf:

  def __init__(self):
    self.buf = []

  def atleast(self, n):
    if len(self.buf) < n:
      # I think to extend we'd need yet another sequence, so new list is good:
      self.buf = [None] * n
    return self.buf

  def __getitem__(self, key):
    return self.buf[key]
