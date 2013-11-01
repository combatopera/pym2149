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
    # We use AND as zero is preferred over envelope, see qbmixenv:
    noiseflag = self.noiseflagreg.value
    if self.toneflagreg.value:
      self.blockbuf.copybuf(self.tone(self.block, self.masked))
      if noiseflag:
        self.blockbuf.andbuf(self.noise(self.block, self.masked))
    elif noiseflag:
      self.blockbuf.copybuf(self.noise(self.block, self.masked))
    else:
      # Fixed and variable levels should work, see qanlgmix and qenvpbuf:
      self.blockbuf.fill(1)

class Multiplexer(Node):

  def __init__(self, *streams):
    Node.__init__(self, self.commondtype(*streams), len(streams))
    self.streams = streams

  def callimpl(self):
    for i, stream in enumerate(self.streams):
      self.blockbuf.putring(i, len(self.streams), stream(self.block, self.masked).buf, 0, self.block.framecount)

class Mixer(Node):

  def __init__(self, container):
    Node.__init__(self, np.int32) # SoX internal sample format.
    self.datum = self.dtype(2 ** 30.5) # Half power point, very close to -3 dB.
    self.container = container

  def callimpl(self):
    self.blockbuf.fill(self.datum)
    for buf in self.container(self.block, self.masked):
      self.blockbuf.subbuf(buf)
