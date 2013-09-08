from nod import Node
from dac import Dac
import numpy as np

class Mixer(Node):

  def __init__(self, *streams):
    Node.__init__(self, np.float32)
    self.streams = streams

  def callimpl(self, block):
    self.blockbuf.fill(0, self.blockbuf.framecount(), -Dac.halfpoweramp)
    for stream in self.streams:
      self.blockbuf.addbuf(stream(block))
