import numpy as np
from buf import MasterBuf, Buf
from minblep import MinBleps
from nod import Node
from wav import Wave16

class WavWriter(Node):

  outrate = 44100

  def __init__(self, clock, chip, path):
    Node.__init__(self)
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
    outcount = self.outz - out0
    # Make space for all samples we can output plus overflow:
    outbuf = self.outmaster.ensureandcrop(outcount + self.overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:self.overflowsize] = self.carrybuf.buf
    outbuf.buf[self.overflowsize:] = self.dc
    def pasteminblep():
      outbuf.buf[outi[idx]:outj[idx]] += mixin[idx]
      outbuf.buf[outj[idx]:] += amp[idx]
    nonzeros = diffbuf.nonzeros()
    outi, shape = self.minbleps.getoutindexandshape(self.naivex + nonzeros)
    outi -= out0
    outj = outi + self.minbleps.mixinsize
    mixin = self.minbleps.getmixin(shape, diffbuf.buf[nonzeros])
    amp = diffbuf.buf[nonzeros]
    # FIXME: This loop is too slow, so get numpy to implement it somehow.
    for idx in xrange(len(nonzeros)):
      pasteminblep()
    wavbuf = self.wavmaster.ensureandcrop(outcount)
    wavbuf.buf[:] = outbuf.buf[:outcount] # Cast to int16.
    self.f.block(wavbuf)
    self.carrybuf.buf[:] = outbuf.buf[outcount:]
    self.naivex += framecount
    self.dc = chipbuf.buf[-1]

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()
