import lfsr, numpy as np
from nod import Node

class Osc(Node):

  def __init__(self, steps, periodreg):
    if 0 != (self.scale % steps):
      raise Exception("Number of steps must divide the scale.")
    Node.__init__(self, np.uint8) # Slightly faster than plain old int.
    self.indexinstep = 0
    self.stepindex = -1
    self.steps = steps
    self.periodreg = periodreg

  def callimpl(self):
    oldperiod = True
    frameindex = 0
    while frameindex < self.block.framecount:
      if not self.indexinstep:
        self.stepindex = (self.stepindex + 1) % self.steps
        if oldperiod and not self.stepindex:
          self.stepsize = self.scale / self.steps * max(1, self.periodreg.value)
          oldperiod = False
        self.value = self.stepvalue(self.stepindex)
      n = min(self.block.framecount - frameindex, self.stepsize - self.indexinstep)
      self.blockbuf.fill(frameindex, frameindex + n, self.value)
      self.indexinstep = (self.indexinstep + n) % self.stepsize
      frameindex += n

class ToneOsc(Osc):

  scale = 16

  def __init__(self, periodreg):
    Osc.__init__(self, 2, periodreg)

  def stepvalue(self, stepindex):
    return 1 - stepindex

class NoiseOsc(Osc):

  scale = 16

  def __init__(self, periodreg):
    # One step per scale results in expected spectrum (and agrees with Hatari):
    Osc.__init__(self, 1, periodreg)
    self.lfsr = lfsr.Lfsr(*lfsr.ym2149nzdegrees)

  def stepvalue(self, stepindex):
    return self.lfsr()
