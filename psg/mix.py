from buf import *
from dac import *

class Mixer:

  def __init__(self, *streams):
    self.buf = SimpleBuf(0)
    self.streams = streams

  def __call__(self, buf):
    self.streams[0](buf)
    tmp = self.buf.crop(buf.framecount())
    for stream in self.streams[1:]:
      stream(tmp)
      buf.add(tmp)
    buf.xform(-Dac.halfpoweramp)
