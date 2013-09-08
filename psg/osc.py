import lfsr, numpy as np
from nod import Node

class Osc(Node):

  def __init__(self, unit, periodreg):
    Node.__init__(self, np.uint8) # Slightly faster than plain old int.
    self.index = 0
    self.value = None
    self.unit = unit
    self.periodreg = periodreg

  def loadperiod(self):
    self.limit = self.unit * self.periodreg.value

  def callimpl(self, block):
    frameindex = 0
    framecount = self.blockbuf.framecount()
    while frameindex < framecount:
      if not self.index:
        self.value = self.nextvalue(self.value, self.loadperiod)
      n = min(framecount - frameindex, self.limit - self.index)
      self.blockbuf.fill(frameindex, frameindex + n, self.value)
      self.index = (self.index + n) % self.limit
      frameindex += n

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
    # Passing in scale as-is results in expected spectrum (and agrees with Hatari):
    Osc.__init__(self, self.scale, periodreg)
    self.lfsr = lfsr.Lfsr(*lfsr.ym2149nzdegrees)

  def nextvalue(self, previous, applyperiod):
    applyperiod() # Unlike for tone, we can change period every flip.
    return self.lfsr()
