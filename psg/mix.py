from nod import Node
from dac import Dac
import numpy as np

class Mixer(Node):

  def __init__(self, *streams):
    Node.__init__(self, np.uint32)
    self.streams = streams

  def callimpl(self):
    self.blockbuf.fill(0, self.block.framecount, Dac.headroom)
    for stream in self.streams:
      self.blockbuf.addbuf(stream(self.block))
