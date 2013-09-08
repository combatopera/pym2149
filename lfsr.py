class Lfsr:

  def __init__(self, *nzdegrees):
    self.mask = sum(1 << (nzd - 1) for nzd in nzdegrees)
    self.x = 1

  def __call__(self):
    bit = self.x & 1
    self.x >>= 1
    if bit:
      self.x ^= self.mask
    return bit

  def __iter__(self):
    first = self.x
    while True:
      yield self()
      if first == self.x:
        break
