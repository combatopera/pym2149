from __future__ import division
import struct, logging, os
from pym2149.ym2149 import stclock

log = logging.getLogger(__name__)

class YM:

  checkstr = 'LeOnArD!'
  wordstruct = struct.Struct('>H')
  lwordstruct = struct.Struct('>I')

  def __init__(self, f, checkstr):
    if checkstr:
      if self.checkstr != f.read(len(self.checkstr)):
        raise Exception('Bad check string.')
    self.f = f

  def word(self):
    return self.wordstruct.unpack(self.f.read(2))[0]

  def lword(self):
    return self.lwordstruct.unpack(self.f.read(4))[0]

  def skip(self, n):
    self.f.seek(n, 1)

  def ntstring(self):
    start = self.f.tell()
    while ord(self.f.read(1)):
      pass
    textlen = self.f.tell() - 1 - start
    self.f.seek(start)
    text = self.f.read(textlen)
    self.skip(1)
    return text

  def interleavedframe(self):
    v = [None] * self.framesize
    for i in xrange(self.framesize - 1):
      v[i] = ord(self.f.read(1))
      self.skip(-1 + self.framecount)
    v[self.framesize - 1] = ord(self.f.read(1))
    self.skip(-(self.framesize - 1) * self.framecount)
    return v

  def simpleframe(self):
    return [ord(c) for c in self.f.read(self.framesize)]

  def close(self):
    self.f.close()

class YM3(YM):

  formatid = 'YM3!'
  framesize = 14
  clock = stclock
  framefreq = 50
  info = ()

  def __init__(self, f):
    YM.__init__(self, f, False)
    self.framecount = (os.fstat(f.fileno()).st_size - len(self.formatid)) // self.framesize

  def __iter__(self):
    for _ in xrange(self.framecount):
      yield self.interleavedframe()

class YM56(YM):

  framesize = 16

  def __init__(self, f):
    YM.__init__(self, f, True)
    self.framecount = self.lword()
    # We can ignore the other attributes as they are specific to sample data:
    interleaved = self.lword() & 0x01
    self.samplecount = self.word()
    self.clock = self.lword()
    self.framefreq = self.word()
    self.loopframe = self.lword()
    self.skip(self.word()) # Future expansion.
    if self.samplecount:
      log.warn("Ignoring %s samples.", self.samplecount)
      for _ in xrange(self.samplecount):
        self.skip(self.lword())
    self.info = tuple(self.ntstring() for _ in xrange(3))
    self.loopoff = self.f.tell()
    if interleaved:
      self.frame = self.interleavedframe
      self.loopoff += self.loopframe
    else:
      self.frame = self.simpleframe
      self.loopoff += self.loopframe * self.framesize

  def __iter__(self):
    for _ in xrange(self.framecount):
      yield self.frame()
    while True:
      self.f.seek(self.loopoff)
      for _ in xrange(self.framecount - self.loopframe)
        yield self.frame()

class YM5(YM56):

  formatid = 'YM5!'

class YM6(YM56):

  formatid = 'YM6!'

impls = dict([i.formatid, i] for i in [YM3, YM5, YM6])

def ymopen(path):
  f = open(path, 'rb')
  try:
    return impls[f.read(4)](f)
  except:
    f.close()
    raise
