from nod import Node
from dac import Dac
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
    if not self.toneflagreg.value:
      self.blockbuf.copybuf(self.tone(self.block))
      if not noiseflag:
        self.blockbuf.orbuf(self.noise(self.block))
    elif noiseflag:
      self.blockbuf.copybuf(self.noise(self.block))
    else:
      self.blockbuf.fill(0)

class Mixer(Node):

  def __init__(self, *streams):
    # TODO: It would be cheap to mix unsigned into SoX-native signed here.
    Node.__init__(self, Node.commondtype(*streams))
    self.streams = streams

  def callimpl(self):
    self.blockbuf.fill(Dac.datum)
    for stream in self.streams:
      self.blockbuf.addbuf(stream(self.block))
