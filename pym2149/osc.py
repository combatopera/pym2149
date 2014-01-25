from __future__ import division
import lfsr, numpy as np, itertools, math
from nod import Node
from dac import leveltoamp, amptolevel

class Values:

  def __init__(self, dtype, g, loop = 0):
    self.buf = np.fromiter(g, dtype)
    self.loop = loop

class OscNode(Node):

  def __init__(self, dtype, periodreg):
    Node.__init__(self, dtype)
    self.reset()
    self.periodreg = periodreg

  def reset(self):
    self.valueindex = 0
    self.progress = self.scaleofstep * 0xffff # Matching biggest possible 16-bit stepsize.

  def getvalue(self, n = 1):
    self.warp(n - 1)
    self.lastvalue = self.values.buf[self.valueindex]
    self.warp(1)
    return self.lastvalue

  def warp(self, n):
    self.valueindex += n
    size = self.values.buf.shape[0]
    while self.valueindex >= size:
      self.valueindex = self.values.loop + self.valueindex - size

  def prolog(self):
    # If progress beats the new stepsize, we terminate right away:
    cursor = min(self.block.framecount, max(0, self.stepsize - self.progress))
    cursor and self.blockbuf.fillpart(0, cursor, self.lastvalue)
    self.progress = min(self.progress + cursor, self.stepsize)
    return cursor

  def common(self, cursor):
    fullsteps = (self.block.framecount - cursor) // self.stepsize
    if self.blockbuf.putringops(self.values.buf, self.valueindex, fullsteps) * self.stepsize < fullsteps:
      for i in xrange(self.stepsize):
        self.blockbuf.putring(cursor + i, self.stepsize, self.values.buf, self.valueindex, fullsteps)
      self.getvalue(fullsteps)
      cursor += fullsteps * self.stepsize
    else:
      for _ in xrange(fullsteps):
        self.blockbuf.fillpart(cursor, cursor + self.stepsize, self.getvalue())
        cursor += self.stepsize
    if cursor < self.block.framecount:
      self.blockbuf.fillpart(cursor, self.block.framecount, self.getvalue())
      self.progress = self.block.framecount - cursor

class ToneOsc(OscNode):

  values = Values(Node.binarydtype, (1 - (i & 1) for i in xrange(1000)))

  def __init__(self, scale, periodreg):
    self.scaleofstep = scale * 2 // 2
    OscNode.__init__(self, Node.binarydtype, periodreg)

  def callimpl(self):
    self.stepsize = self.scaleofstep * self.periodreg.value
    cursor = self.prolog()
    if cursor < self.block.framecount:
      self.common(cursor)

class NoiseOsc(OscNode):

  values = Values(Node.binarydtype, lfsr.Lfsr(*lfsr.ym2149nzdegrees))

  def __init__(self, scale, periodreg):
    self.scaleofstep = scale * 2 # This results in authentic spectrum, see qnoispec.
    OscNode.__init__(self, Node.binarydtype, periodreg)
    self.stepsize = self.progress

  def callimpl(self):
    cursor = self.prolog()
    if cursor < self.block.framecount:
      self.progress = self.stepsize = self.scaleofstep * self.periodreg.value
      self.common(cursor)

def cycle(v, minsize): # Unlike itertools version, we assume v can be iterated more than once.
  for _ in xrange((minsize + len(v) - 1) // len(v)):
    for x in v:
      yield x

def sinevalues(steps): # Like saw but unlike triangular, we use steps for a full wave.
  levels = []
  minamp = leveltoamp(0)
  for i in xrange(steps):
    amp = minamp + (1 - minamp) * (math.sin(2 * math.pi * i / steps) + 1) / 2
    levels.append(round(amptolevel(amp)))
  return Values(Node.zto255dtype, cycle(levels, 1000))

class EnvOsc(OscNode):

  steps = 32
  values0c = Values(Node.zto255dtype, cycle(range(steps), 1000))
  values08 = Values(Node.zto255dtype, cycle(range(steps - 1, -1, -1), 1000))
  values0e = Values(Node.zto255dtype, cycle(range(steps) + range(steps - 1, -1, -1), 1000))
  values0a = Values(Node.zto255dtype, cycle(range(steps - 1, -1, -1) + range(steps), 1000))
  values0f = Values(Node.zto255dtype, itertools.chain(xrange(steps), itertools.repeat(0, 1000)), steps)
  values0d = Values(Node.zto255dtype, itertools.chain(xrange(steps), itertools.repeat(steps - 1, 1000)), steps)
  values0b = Values(Node.zto255dtype, itertools.chain(xrange(steps - 1, -1, -1), itertools.repeat(steps - 1, 1000)), steps)
  values09 = Values(Node.zto255dtype, itertools.chain(xrange(steps - 1, -1, -1), itertools.repeat(0, 1000)), steps)
  values10 = sinevalues(steps)

  def __init__(self, scale, periodreg, shapereg):
    self.scaleofstep = scale * 32 // self.steps
    OscNode.__init__(self, Node.zto255dtype, periodreg)
    self.shapeversion = None
    self.shapereg = shapereg

  def callimpl(self):
    if self.shapeversion != self.shapereg.version:
      shape = self.shapereg.value
      if shape == (shape & 0x07):
        shape = (0x09, 0x0f)[bool(shape & 0x04)]
      self.values = getattr(self, "values%02x" % shape)
      self.shapeversion = self.shapereg.version
      self.reset()
    self.stepsize = self.scaleofstep * self.periodreg.value
    cursor = self.prolog()
    if cursor < self.block.framecount:
      self.common(cursor)
