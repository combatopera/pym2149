import lfsr

class Osc:

  def __init__(self, unit):
    self.unit = unit
    self.index = 0
    self.value = None

  def setperiod(self, period):
    self.period = period

  def __call__(self):
    if not self.index:
      def applyperiod():
        self.limit = self.unit * self.period
      self.value = self.nextvalue(self.value, applyperiod)
    self.index = (self.index + 1) % self.limit
    return self.value

class ToneOsc(Osc):

  def __init__(self):
    # Divide count by 2 so that the whole wave is 16:
    Osc.__init__(self, 16 / 2)

  def nextvalue(self, previous, applyperiod):
    if not previous: # Includes initial case.
      applyperiod()
      return 1
    else:
      return 0

class NoiseOsc(Osc):

  def __init__(self):
    # Halve the count so that the upper frequency bound is correct:
    Osc.__init__(self, 16 / 2)
    self.lfsr = lfsr.Lfsr(*lfsr.ym2149nzdegrees)

  def nextvalue(self, previous, applyperiod):
    applyperiod() # Unlike for tone, we can change period every half-wave.
    return self.lfsr()
