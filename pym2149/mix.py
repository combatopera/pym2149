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
    # We choose OR as that's what Steem appears to use:
    self.blockbuf.fill(0)
    if not self.toneflagreg.value:
      self.blockbuf.orbuf(self.tone(self.block))
    if not self.noiseflagreg.value:
      self.blockbuf.orbuf(self.noise(self.block))

class Mixer(Node):

  def __init__(self, *streams):
    Node.__init__(self, Node.commondtype(*streams))
    self.streams = streams

  def callimpl(self):
    self.blockbuf.fill(Dac.headroom)
    for stream in self.streams:
      self.blockbuf.addbuf(stream(self.block))
