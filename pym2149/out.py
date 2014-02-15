import numpy as np, sys, errno
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
    try:
      filesize = self.f.tell()
    except IOError, e:
      if errno.ESPIPE != e.errno:
        raise
      return # Leave huge sizes.
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
    # XXX: Why does a tenth of ideal scale look better than ideal scale itself?
    scale = 1000 # Smaller values result in worse-looking spectrograms.
    dtype = np.float32 # Effectively about 24 bits.
    self.diffmaster = MasterBuf(dtype = dtype)
    self.outmaster = MasterBuf(dtype = dtype)
    self.wavmaster = MasterBuf(dtype = np.int16)
    self.minbleps = MinBleps(clock, self.outrate, scale)
    # Need space for a whole mixin in case it is rooted at outz:
    self.overflowsize = self.minbleps.mixinsize
    self.carrybuf = Buf(np.empty(self.overflowsize, dtype = dtype))
    self.f = Wave16(path, self.outrate)
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.outz = 0 # Absolute index of first output sample being processed in this iteration.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.chip = chip

  def callimpl(self):
    chipbuf = self.chain(self.chip)
    framecount = len(chipbuf)
    diffbuf = self.diffmaster.differentiate(self.dc, chipbuf)
    out0 = self.outz
    # Index of the first sample we can't output yet:
    self.outz = self.minbleps.getoutindexandshape(self.naivex + framecount)[0]
    # Make space for all samples we can output plus overflow:
    outbuf = self.outmaster.ensureandcrop(self.outz - out0 + self.overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:self.overflowsize] = self.carrybuf.buf
    outbuf.buf[self.overflowsize:] = self.dc
    def pasteminblep():
      amp = diffbuf.buf[naivey]
      outj = outi[idx] + self.minbleps.mixinsize
      outbuf.buf[outi[idx] - out0:outj - out0] += mixin[idx]
      outbuf.buf[outj - out0:] += amp
    nonzeros = diffbuf.nonzeros()
    outi, shape = self.minbleps.getoutindexandshape(self.naivex + nonzeros)
    mixin = self.minbleps.getmixin(shape, diffbuf.buf[nonzeros])
    # FIXME: This loop is too slow, so get numpy to implement it somehow.
    for idx, naivey in enumerate(nonzeros):
      pasteminblep()
    wavbuf = self.wavmaster.ensureandcrop(self.outz - out0)
    wavbuf.buf[:] = outbuf.buf[:self.outz - out0] # Cast to int16.
    self.f.block(wavbuf)
    self.carrybuf.buf[:] = outbuf.buf[self.outz - out0:]
    self.naivex += framecount
    self.dc = chipbuf.buf[-1]

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()
