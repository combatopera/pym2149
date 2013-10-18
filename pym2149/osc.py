from __future__ import division
import lfsr, numpy as np
from nod import Node

class OscNode(Node):

  oscdtype = np.uint8 # Slightly faster than plain old int.

  def __init__(self, periodreg):
    Node.__init__(self, self.oscdtype)
    self.valueindex = 0
    self.periodreg = periodreg

  def lastvalue(self):
    return self.values.buf[self.valueindex - 1]

  def getvalue(self):
    v = self.values.buf[self.valueindex]
    self.advance(1)
    return v

  def advance(self, n):
    self.valueindex = (self.valueindex + n) % self.values.buf.shape[0]

class Values:

  def __init__(self, g, loop = 0):
    self.buf = np.fromiter(g, OscNode.oscdtype)
    self.loop = loop

class ToneOsc(OscNode):

  halfscale = 16 // 2
  values = Values(1 - (i & 1) for i in xrange(1000))

  def __init__(self, periodreg):
    OscNode.__init__(self, periodreg)
    self.progress = self.halfscale * 0xfff # Matching biggest possible stepsize.

  def callimpl(self):
    self.stepsize = self.halfscale * self.periodreg.value
    # If progress beats the new stepsize, we terminate right away:
    cursor = min(self.block.framecount, max(0, self.stepsize - self.progress))
    cursor and self.blockbuf.fillpart(0, cursor, self.lastvalue())
    self.progress = min(self.progress + cursor, self.stepsize)
    if cursor == self.block.framecount:
      return
    fullsteps = (self.block.framecount - cursor) // self.stepsize
    if self.blockbuf.putringops(self.values.buf, self.valueindex, fullsteps) * self.stepsize < fullsteps:
      for i in xrange(self.stepsize):
        self.blockbuf.putring(cursor + i, self.stepsize, self.values.buf, self.valueindex, fullsteps)
      self.advance(fullsteps)
      cursor += fullsteps * self.stepsize
    else:
      for _ in xrange(fullsteps):
        self.blockbuf.fillpart(cursor, cursor + self.stepsize, self.getvalue())
        cursor += self.stepsize
    if cursor == self.block.framecount:
      return
    self.blockbuf.fillpart(cursor, self.block.framecount, self.getvalue())
    self.progress = self.block.framecount - cursor

class NoiseOsc(OscNode):

  scale = 16
  values = Values(lfsr.Lfsr(*lfsr.ym2149nzdegrees))

  def __init__(self, periodreg):
    OscNode.__init__(self, periodreg)
    self.progress = self.stepsize = 0

  def callimpl(self):
    cursor = min(self.block.framecount, self.stepsize - self.progress)
    cursor and self.blockbuf.fillpart(0, cursor, self.lastvalue())
    self.progress += cursor
    if cursor == self.block.framecount:
      return
    # One step per scale results in authentic spectrum, see qnoispec:
    self.stepsize = self.scale * self.periodreg.value
    fullsteps = (self.block.framecount - cursor) // self.stepsize
    if self.blockbuf.putringops(self.values.buf, self.valueindex, fullsteps) * self.stepsize < fullsteps:
      for i in xrange(self.stepsize):
        self.blockbuf.putring(cursor + i, self.stepsize, self.values.buf, self.valueindex, fullsteps)
      self.advance(fullsteps)
      cursor += fullsteps * self.stepsize
    else:
      for _ in xrange(fullsteps):
        self.blockbuf.fillpart(cursor, cursor + self.stepsize, self.getvalue())
        cursor += self.stepsize
    if cursor == self.block.framecount:
      self.progress = self.stepsize # Necessary in case stepsize changed.
      return
    self.blockbuf.fillpart(cursor, self.block.framecount, self.getvalue())
    self.progress = self.block.framecount - cursor

class EnvOsc(OscNode):

  scale = 256
  steps = 32

  def __init__(self, periodreg, shapereg):
    OscNode.__init__(self, periodreg)
    self.reset()
    self.shapeversion = None
    self.shapereg = shapereg

  def reset(self):
    self.indexinstep = 0
    self.stepindex = -1
    self.periodindex = -1

  def callimpl(self):
    if self.shapeversion != self.shapereg.version:
      shape = self.shapereg.value & 0x0f
      if not (shape & 0x08):
        shape = (0x09, 0x0f)[bool(shape & 0x04)]
      self.stepvalue = getattr(self, "stepvalue%02x" % shape)
      self.shapeversion = self.shapereg.version
      self.reset()
    oldperiod = True
    frameindex = 0
    while frameindex < self.block.framecount:
      if not self.indexinstep:
        self.stepindex = (self.stepindex + 1) % self.steps
        if not self.stepindex:
          self.periodindex += 1
          if oldperiod:
            self.stepsize = self.scale // self.steps * self.periodreg.value
            oldperiod = False
        self.value = self.stepvalue(self.stepindex)
      n = min(self.block.framecount - frameindex, self.stepsize - self.indexinstep)
      self.blockbuf.fillpart(frameindex, frameindex + n, self.value)
      self.indexinstep = (self.indexinstep + n) % self.stepsize
      frameindex += n

  def stepvalue08(self, stepindex):
    return 31 - stepindex

  def stepvalue09(self, stepindex):
    if not self.periodindex:
      return 31 - stepindex
    else:
      return 0

  def stepvalue0a(self, stepindex):
    if not (self.periodindex & 1):
      return 31 - stepindex
    else:
      return stepindex

  def stepvalue0b(self, stepindex):
    if not self.periodindex:
      return 31 - stepindex
    else:
      return 31

  def stepvalue0c(self, stepindex):
    return stepindex

  def stepvalue0d(self, stepindex):
    if not self.periodindex:
      return stepindex
    else:
      return 31

  def stepvalue0e(self, stepindex):
    if not (self.periodindex & 1):
      return stepindex
    else:
      return 31 - stepindex

  def stepvalue0f(self, stepindex):
    if not self.periodindex:
      return stepindex
    else:
      return 0
