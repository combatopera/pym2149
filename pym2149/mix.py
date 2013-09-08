from nod import Node
import numpy as np

class BinMix(Node):

  def __init__(self, tone, noise, toneflagreg, noiseflagreg):
    Node.__init__(self, Node.commondtype(tone, noise))
    self.tone = tone
    self.noise = noise
    self.toneflagreg = toneflagreg
    self.noiseflagreg = noiseflagreg

  def callimpl(self):
    # The truth table options are {AND, OR, XOR}.
    # Other functions are negations of these, the 2 constants, or not symmetric.
    # XOR sounds just like noise so it can't be that.
    # AND and OR have the same frequency spectrum so either is good.
    # We use OR as downstream it will prefer envelope shape over zero:
    noiseflag = self.noiseflagreg.value
    if self.toneflagreg.value:
      self.blockbuf.copybuf(self.tone(self.block))
      if noiseflag:
        self.blockbuf.orbuf(self.noise(self.block))
    elif noiseflag:
      self.blockbuf.copybuf(self.noise(self.block))
    else:
      self.blockbuf.fill(0)

class Mixer(Node):

  def __init__(self, *streams):
    Node.__init__(self, np.int32) # SoX internal sample format.
    self.datum = self.dtype(2 ** 30.5) # Half power point, very close to -3 dB.
    self.streams = streams

  def callimpl(self):
    self.blockbuf.fill(self.datum)
    for stream in self.streams:
      self.blockbuf.subbuf(stream(self.block))
