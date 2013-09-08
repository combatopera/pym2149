import lfsr

class Osc:

  def __init__(self, unit, periodreg):
    self.unit = unit
    self.index = 0
    self.value = None
    self.periodreg = periodreg

  def loadperiod(self):
    self.limit = self.unit * self.periodreg.value

  def __call__(self, buf, bufstart, bufstop):
    while bufstart < bufstop:
      if not self.index:
        self.value = self.nextvalue(self.value, self.loadperiod)
      n = min(bufstop - bufstart, self.limit - self.index)
      for bufindex in xrange(bufstart, bufstart + n):
        buf[bufindex] = self.value
      self.index = (self.index + n) % self.limit
      bufstart += n

class ToneOsc(Osc):

  scale = 16

  def __init__(self, periodreg):
    # Divide count by 2 so that the whole wave is 16:
    Osc.__init__(self, self.scale / 2, periodreg)

  def nextvalue(self, previous, applyperiod):
    if not previous: # Includes initial case.
      applyperiod()
      return 1
    else:
      return 0

class NoiseOsc(Osc):

  scale = 16

  def __init__(self, periodreg):
    # Halve the count so that the upper frequency bound is correct:
    Osc.__init__(self, self.scale / 2, periodreg)
    self.lfsr = lfsr.Lfsr(*lfsr.ym2149nzdegrees)

  def nextvalue(self, previous, applyperiod):
    applyperiod() # Unlike for tone, we can change period every half-wave.
    return self.lfsr()
