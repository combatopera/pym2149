import numpy as np, sys
from buf import MasterBuf, Buf
from minblep import MinBleps
from nod import AbstractNode

class Wave16:

  bytespersample = 2
  hugefilesize = 0x80000000

  def __init__(self, path, rate):
    if '-' == path:
      self.f = sys.stdout
    else:
      self.f = open(path, 'wb') # Binary.
    self.f.write('RIFF')
    self.riffsizeoff = 4
    self.writeriffsize(self.hugefilesize)
    self.f.write('WAVEfmt ') # Observe trailing space.
    self.writen(16) # Chunk data size.
    self.writen(1, 2) # PCM (uncompressed).
    channels = 1
    self.writen(channels, 2)
    self.writen(rate)
    bytesperframe = self.bytespersample * channels
    self.writen(rate * bytesperframe) # Bytes per second.
    self.writen(bytesperframe, 2)
    self.writen(self.bytespersample * 8, 2) # Bits per sample.
    self.f.write('data')
    self.datasizeoff = 40
    self.writedatasize(self.hugefilesize)
    self.adjustsizes()

  def writeriffsize(self, filesize):
    self.writen(filesize - (self.riffsizeoff + 4))

  def writedatasize(self, filesize):
    self.writen(filesize - (self.datasizeoff + 4))

  def writen(self, n, size = 4):
    for _ in xrange(size):
      self.f.write(chr(n & 0xff))
      n >>= 8

  def block(self, buf):
    buf.tofile(self.f)
    self.adjustsizes()

  def adjustsizes(self):
    filesize = self.f.tell()
    self.f.seek(self.riffsizeoff)
    self.writeriffsize(filesize)
    self.f.seek(self.datasizeoff)
    self.writedatasize(filesize)
    self.f.seek(filesize)

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()

class WavWriter(AbstractNode):

  outrate = 44100

  def __init__(self, clock, chip, path):
    AbstractNode.__init__(self)
    scale = 500 # Smaller values result in worse-looking spectrograms.
    dtype = np.float32 # Effectively about 24 bits.
    self.diffmaster = MasterBuf(dtype = dtype)
    self.outmaster = MasterBuf(dtype = dtype)
    self.wavmaster = MasterBuf(dtype = np.int16)
    self.minbleps = MinBleps(clock, self.outrate, scale)
    # One less than max mixin size, sufficient for any mixin at last sample:
    self.overflowsize = self.minbleps.mixin1size
    self.carrybuf = Buf(np.empty(self.overflowsize, dtype = dtype))
    self.f = Wave16(path, self.outrate)
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.outz = 0 # Absolute index of first output sample being processed in this iteration.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.chip = chip

  def callimpl(self):
    blockbuf = self.chain(self.chip)
    framecount = len(blockbuf)
    diffbuf = self.diffmaster.differentiate(self.dc, blockbuf)
    out0 = self.outz
    # Index of the first sample we can't output yet:
    self.outz = self.minbleps.getoutindexandshape(self.naivex + framecount)[0]
    # Make space for all samples we can output plus overflow:
    outbuf = self.outmaster.ensureandcrop(self.outz - out0 + self.overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:self.overflowsize] = self.carrybuf.buf
    outbuf.buf[self.overflowsize:] = self.dc
    for naivey in diffbuf.nonzeros():
      amp = diffbuf.buf[naivey]
      outi, mixin, mixinsize = self.minbleps.getmixin(self.naivex + naivey, amp)
      outj = outi + mixinsize
      outbuf.buf[outi - out0:outj - out0] += mixin
      outbuf.buf[outj - out0:] += amp
    wavbuf = self.wavmaster.ensureandcrop(self.outz - out0)
    wavbuf.buf[:] = outbuf.buf[:self.outz - out0]
    self.f.block(wavbuf)
    self.carrybuf.buf[:] = outbuf.buf[self.outz - out0:]
    self.naivex += framecount
    self.dc = blockbuf.buf[-1]

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()
