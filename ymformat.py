import struct, logging

log = logging.getLogger(__name__)

class YMFile:

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

  def close(self):
    self.f.close()

class YM6File(YMFile):

  formatid = 'YM6!'
  framesize = 16

  def __init__(self, f):
    YMFile.__init__(self, f, True)
    self.framecount = self.lword()
    # TODO LATER: There are more attributes.
    self.frame = [self.simpleframe, self.interleavedframe][self.lword() & 1]
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

  def simpleframe(self): # Not tested.
    return [ord(c) for c in self.f.read(self.framesize)]

  def interleavedframe(self):
    # FIXME: Too slow.
    v = [None] * self.framesize
    for i in xrange(self.framesize - 1):
      v[i] = ord(self.f.read(1))
      self.skip(-1 + self.framecount)
    v[self.framesize - 1] = ord(self.f.read(1))
    self.skip(-(self.framesize - 1) * self.framecount)
    return v

  def __iter__(self): # FIXME: Does not loop.
    for _ in xrange(self.framecount):
      yield self.frame()

impls = dict([i.formatid, i] for i in [YM6File])

def ymopen(path):
  f = open(path, 'rb')
  try:
    return impls[f.read(4)](f)
  except:
    f.close()
    raise
