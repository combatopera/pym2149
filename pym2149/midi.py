class Patch:

  def __init__(self, chip, nominalclock, index):
    self.chip = chip
    self.nominalclock = nominalclock
    self.index = index

  def noteon(self, pitch): pass

  def noteonframe(self, frame): pass

  def noteoff(self): pass

  def noteoffframe(self, frame): pass

class DefaultPatch(Patch):

  def noteon(self, pitch):
    self.chip.toneperiods[self.index].value = pitch.freq().toneperiod(self.nominalclock)
    self.chip.toneflags[self.index].value = True
    self.chip.fixedlevels[self.index].value = 15

  def noteoffframe(self, frame):
    self.chip.fixedlevels[self.index].value = max(14 - frame, 0)
