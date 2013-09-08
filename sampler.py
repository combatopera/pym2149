class Sampler:

  def __init__(self, signal, ratio):
    self.signal = signal
    self.ratio = ratio
    self.vindex = -1
    self.v = 0
    self.pos = 0

  def __call__(self):
    while True:
      vfactor = self.pos - self.vindex + 1
      if vfactor <= 1:
        break
      self.u = self.v
      self.v = self.signal()
      self.vindex += 1
    self.pos += self.ratio
    return (1 - vfactor) * self.u + vfactor * self.v
