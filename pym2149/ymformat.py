# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import struct, logging, os, tempfile, subprocess, shutil, sys
from pym2149.ym2149 import stclock
from fractions import Fraction

log = logging.getLogger(__name__)

class LoopInfo:

  def __init__(self, frame, offset):
    self.frame = frame
    self.offset = offset

class YM:

  checkstr = 'LeOnArD!'
  wordstruct = struct.Struct('>H')
  lwordstruct = struct.Struct('>I')
  lwordlestruct = struct.Struct('<I')

  @staticmethod
  def logignoringloopinfo():
    log.debug('Ignoring loop info.')

  def __init__(self, f, expectcheckstr):
    log.debug("Format ID: %s", self.formatid)
    if expectcheckstr:
      if self.checkstr != f.read(len(self.checkstr)):
        raise Exception('Bad check string.')
    self.frameindex = 0
    self.f = f

  def number(self, struct):
    return struct.unpack(self.f.read(struct.size))[0]

  def word(self):
    return self.number(self.wordstruct)

  def lword(self):
    return self.number(self.lwordstruct)

  def readloopframe(self):
    loopframe = self.lword()
    if loopframe < self.framecount:
      return loopframe
    self.skip(-4)
    loopframe = self.number(self.lwordlestruct)
    if loopframe < self.framecount:
      log.info('Loop frame apparently little-endian.')
      return loopframe
    loopframe = 0
    log.warn("Cannot interpret loop frame, defaulting to %s.", loopframe)
    return loopframe

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

  def step(self):
    frame = self.frameobj(self)
    self.frameindex += 1
    return frame

  def __iter__(self):
    while self.frameindex < self.framecount:
      yield self.step()
    if self.loopinfo is None:
      return
    while True:
      if not (self.frameindex - self.framecount) % (self.framecount - self.loopinfo.frame):
        log.debug("Looping to frame %s.", self.loopinfo.frame)
        self.f.seek(self.loopinfo.offset)
      yield self.step()

  def close(self):
    self.f.close()

class PlainFrame:

  def __init__(self, ym):
    self.data = ym.readframe()

  def __call__(self, chip):
    for i, x in enumerate(self.data):
      if 0xD != i or 255 != x:
        chip.R[i].value = x

class YM23(YM):

  framesize = 14
  clock = stclock
  framefreq = 50
  info = ()
  readframe = YM.interleavedframe
  loopinfo = None # Default, overridden in YM3b.
  frameobj = PlainFrame

  def __init__(self, f):
    YM.__init__(self, f, False)
    self.framecount = (os.fstat(f.fileno()).st_size - len(self.formatid)) // self.framesize

class YM2(YM23): # FIXME: Work out format from ST-Sound source, it's not this simple.

  formatid = 'YM2!'

  def __init__(self, f, config):
    YM23.__init__(self, f)

class YM3(YM23):

  formatid = 'YM3!'

  def __init__(self, f, config):
    YM23.__init__(self, f)

class YM3b(YM23):

  formatid = 'YM3b'

  def __init__(self, f, config):
    YM23.__init__(self, f)
    if config.once:
      self.logignoringloopinfo()
    else:
      self.skip(self.framecount * self.framesize)
      loopframe = self.readloopframe()
      self.skip(-(self.framecount * self.framesize + 4))
      self.loopinfo = LoopInfo(loopframe, self.f.tell() + loopframe)

class YM56(YM):

  framesize = 16

  def __init__(self, f, config):
    YM.__init__(self, f, True)
    self.framecount = self.lword()
    # We can ignore the other attributes as they are specific to sample data:
    interleaved = self.lword() & 0x01
    samplecount = self.word()
    self.clock = self.lword()
    self.framefreq = self.word()
    loopframe = self.readloopframe()
    self.skip(self.word()) # Future expansion.
    if samplecount:
      log.warn("Ignoring %s samples.", samplecount)
      for _ in xrange(samplecount):
        self.skip(self.lword())
    self.info = tuple(self.ntstring() for _ in xrange(3))
    dataoffset = self.f.tell()
    if interleaved:
      self.readframe = self.interleavedframe
    else:
      self.readframe = self.simpleframe
    if config.once:
      self.logignoringloopinfo()
      self.loopinfo = None
    elif interleaved:
      self.loopinfo = LoopInfo(loopframe, dataoffset + loopframe)
    else:
      self.loopinfo = LoopInfo(loopframe, dataoffset + loopframe * self.framesize)
    self.logtimersynth = True
    self.logdigidrum = True

class Frame56(PlainFrame):

  mfpclock = 2457600
  prescalers = (0, 4, 10, 16, 50, 64, 100, 200)

  def __init__(self, ym):
    PlainFrame.__init__(self, ym)
    self.index = ym.frameindex
    self.flags = ym

class Frame5(Frame56):

  def __call__(self, chip):
    PlainFrame.__call__(self, chip)
    if self.flags.logtimersynth and (self.data[0x1] & 0x30):
      log.warn("Timer-synth at frame %s.", self.index)
      self.flags.logtimersynth = False
    if self.flags.logdigidrum and (self.data[0x3] & 0x30):
      log.warn("Digi-drum at frame %s.", self.index)
      self.flags.logdigidrum = False

class Frame6(Frame56):

  def __call__(self, chip):
    PlainFrame.__call__(self, chip)
    for flag in chip.tsflags:
      flag.value = False
    for r, rr, rrr in [0x1, 0x6, 0xE], [0x3, 0x8, 0xF]:
      if self.data[r] & 0x30:
        chan = ((self.data[r] & 0x30) >> 4) - 1
        fx = self.data[r] & 0xc0
        if 0x00 == fx:
          denom = self.prescalers[(self.data[rr] & 0xe0) >> 5] * self.data[rrr]
          if denom:
            chip.tsfreqs[chan].value = Fraction(self.mfpclock, denom)
            chip.tsflags[chan].value = True
        if self.flags.logdigidrum and 0x40 == fx:
          log.warn("Digi-drum at frame %s.", self.index)
          self.flags.logdigidrum = False
        if self.flags.logsinussid and 0x80 == fx:
          log.warn("Sinus-SID at frame %s.", self.index)
          self.flags.logsinussid = False
        if self.flags.logsyncbuzzer and 0xc0 == fx:
          log.warn("Sync-buzzer at frame %s.", self.index)
          self.flags.logsyncbuzzer = False

class YM5(YM56):

  formatid = 'YM5!'
  frameobj = Frame5

class YM6(YM56):

  formatid = 'YM6!'
  frameobj = Frame6

  def __init__(self, *args, **kwargs):
    YM56.__init__(self, *args, **kwargs)
    self.logsinussid = True
    self.logsyncbuzzer = True

impls = dict([i.formatid, i] for i in [YM2, YM3, YM3b, YM5, YM6])

def ymopen(path, config):
  f = open(path, 'rb')
  try:
    if 'YM' == f.read(2):
      return impls['YM' + f.read(2)](f, config)
  except:
    f.close()
    raise
  f.close()
  f = UnpackedFile(path)
  try:
    return impls[f.read(4)](f, config)
  except:
    f.close()
    raise

class UnpackedFile:

  def __init__(self, path):
    self.tmpdir = tempfile.mkdtemp()
    try:
      # Observe we redirect stdout so it doesn't get played:
      subprocess.check_call(['lha', 'x', os.path.abspath(path)], cwd = self.tmpdir, stdout = sys.stderr)
      name, = os.listdir(self.tmpdir)
      self.f = open(os.path.join(self.tmpdir, name), 'rb')
    except:
      self.clean()
      raise

  def clean(self):
    log.debug("Deleting temporary folder: %s", self.tmpdir)
    shutil.rmtree(self.tmpdir)

  def __getattr__(self, name):
    return getattr(self.f, name)

  def close(self):
    self.f.close()
    self.clean()
