#!/usr/bin/env python

from __future__ import division
import numpy as np, random
from pym2149.buf import MasterBuf, Buf
from pym2149.minblep import MinBleps

class Wave16:

  bytespersample = 2

  def __init__(self, path, rate):
    self.f = open(path, 'wb') # Binary.
    self.f.write('RIFF')
    self.skip(4)
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
    self.skip(4)

  def skip(self, n):
    self.f.seek(n, 1)

  def writen(self, n, size = 4):
    for _ in xrange(size):
      self.f.write(chr(n & 0xff))
      n >>= 8

  def block(self, buf):
    buf.tofile(self.f)

  def close(self):
    fsize = self.f.tell()
    self.f.seek(4)
    self.writen(fsize - 8) # Size of RIFF.
    self.f.seek(40)
    self.writen(fsize - 44) # Size of data.
    self.f.close()

def main():
  import subprocess, sys
  naiverate = 2000000
  outrate = 44100
  tonefreq = 1500
  toneamp = .25 * 2 ** 15
  scale = 500 # Smaller values result in worse-looking spectrograms.
  naivesize = naiverate * 60 # One minute of data.
  dtype = np.float32 # Effectively about 24 bits.
  toneoscscale = 16 # A property of the chip.
  periodreg = int(round(naiverate / (toneoscscale * tonefreq)))
  period = toneoscscale * periodreg # Even.
  diffmaster = MasterBuf(dtype = dtype)
  outmaster = MasterBuf(dtype = dtype)
  wavmaster = MasterBuf(dtype = np.int16)
  mixinmaster = MasterBuf(dtype = dtype)
  naivebuf = Buf(np.empty(naivesize, dtype = dtype))
  x = 0
  while x < naivesize:
    naivebuf.fillpart(x, x + period // 2, toneamp)
    naivebuf.fillpart(x + period // 2, x + period, -toneamp)
    x += period
  minbleps = MinBleps(scale)
  overflowsize = minbleps.maxmixinsize() - 1 # Sufficient for any mixin at last sample.
  carrybuf = Buf(np.empty(overflowsize, dtype = dtype))
  f = Wave16('minbleppoc.wav', outrate)
  naivex = 0
  dc = 0 # Last naive value of previous block.
  outz = 0 # Absolute index of first output sample being processed in this iteration.
  carrybuf.fill(dc) # Initial carry can be the initial dc level.
  while naivex < naivesize:
    blocksize = random.randint(1, 30000)
    block = Buf(naivebuf.buf[naivex:naivex + blocksize])
    diffbuf = diffmaster.differentiate(dc, block)
    out0 = outz
    # Index of the first sample we can't output yet:
    outz = minbleps.getoutindexandshape(naivex + blocksize, naiverate, outrate)[0]
    # Make space for all samples we can output plus overflow:
    outbuf = outmaster.ensureandcrop(outz - out0 + overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:overflowsize] = carrybuf.buf
    outbuf.buf[overflowsize:] = dc
    for naivey in diffbuf.nonzeros():
      amp = diffbuf.buf[naivey]
      outi, mixin, mixinsize = minbleps.getmixin(naivex + naivey, naiverate, outrate, amp, mixinmaster)
      outj = outi + mixinsize
      outbuf.buf[outi - out0:outj - out0] += mixin.buf
      outbuf.buf[outj - out0:] += amp
    wavbuf = wavmaster.ensureandcrop(outz - out0)
    wavbuf.buf[:] = outbuf.buf[:outz - out0]
    f.block(wavbuf)
    carrybuf.buf[:] = outbuf.buf[outz - out0:]
    naivex += blocksize
    dc = block.buf[-1]
    del diffbuf, outbuf, wavbuf # Otherwise numpy complains on resize.
  f.close()

if __name__ == '__main__':
  main()
