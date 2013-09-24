from __future__ import division
import struct, logging, os
from pym2149.ym2149 import stclock

log = logging.getLogger(__name__)

class YM:

  checkstr = 'LeOnArD!'
  wordstruct = struct.Struct('>H')
  lwordstruct = struct.Struct('>I')

  def __init__(self, f, expectcheckstr):
    if expectcheckstr:
      if self.checkstr != f.read(len(self.checkstr)):
        raise Exception('Bad check string.')
    self.frameindex = 0
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
    frame = [None] * self.framesize
    for i in xrange(self.framesize - 1):
      frame[i] = ord(self.f.read(1))
      self.skip(-1 + self.framecount)
    frame[self.framesize - 1] = ord(self.f.read(1))
    self.skip(-(self.framesize - 1) * self.framecount)
    return frame

  def simpleframe(self):
    return [ord(c) for c in self.f.read(self.framesize)]

  def __iter__(self):
    while self.frameindex < self.framecount:
      frame = self.readframe()
      self.frameindex += 1
      yield frame
    if self.loopframe is None:
      return
    while True:
      if not (self.frameindex - self.framecount) % (self.framecount - self.loopframe):
        self.f.seek(self.loopoff)
      frame = self.readframe()
      self.frameindex += 1
      yield frame

  def close(self):
    self.f.close()

class YM23(YM):

  framesize = 14
  clock = stclock
  framefreq = 50
  info = ()
  readframe = YM.interleavedframe
  loopframe = None # Default, overridden in YM3b.

  def __init__(self, f):
    YM.__init__(self, f, False)
    self.framecount = (os.fstat(f.fileno()).st_size - len(self.formatid)) // self.framesize

class YM2(YM23):

  formatid = 'YM2!'

class YM3(YM23):

  formatid = 'YM3!'

class YM3b(YM23):

  formatid = 'YM3b'

  def __init__(self, f):
    YM23.__init__(self, f)
    self.skip(self.framecount * self.framesize)
    self.loopframe = self.lword()
    self.skip(-(self.framecount * self.framesize + 4))
    self.loopoff = self.f.tell() + self.loopframe

class YM56(YM):

  framesize = 16

  def __init__(self, f):
    YM.__init__(self, f, True)
    self.framecount = self.lword()
    # We can ignore the other attributes as they are specific to sample data:
    interleaved = self.lword() & 0x01
    samplecount = self.word()
    self.clock = self.lword()
    self.framefreq = self.word()
    self.loopframe = self.lword()
    self.skip(self.word()) # Future expansion.
    if samplecount:
      log.warn("Ignoring %s samples.", samplecount)
      for _ in xrange(samplecount):
        self.skip(self.lword())
    self.info = tuple(self.ntstring() for _ in xrange(3))
    self.loopoff = self.f.tell()
    if interleaved:
      self.readframe = self.interleavedframe
      self.loopoff += self.loopframe
    else:
      self.readframe = self.simpleframe
      self.loopoff += self.loopframe * self.framesize

class YM5(YM56):

  formatid = 'YM5!'

class YM6(YM56):

  formatid = 'YM6!'

impls = dict([i.formatid, i] for i in [YM2, YM3, YM3b, YM5, YM6])

def ymopen(path):
  f = open(path, 'rb')
  try:
    return impls[f.read(4)](f)
  except:
    f.close()
    raise
