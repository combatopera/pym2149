import numpy as np
from buf import MasterBuf, Buf
from minblep import MinBleps
from nod import Node, BufNode
from wav import Wave16

class WavWriter(Node):

  outrate = 44100

  def __init__(self, clock, chip, path):
    Node.__init__(self)
    # XXX: Why does a tenth of ideal scale look better than ideal scale itself?
    scale = 1000 # Smaller values result in worse-looking spectrograms.
    self.diffmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.outmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.wavmaster = MasterBuf(dtype = Wave16.dtype)
    self.minbleps = MinBleps(clock, self.outrate, scale)
    # Need space for a whole mixin in case it is rooted at outz:
    self.overflowsize = self.minbleps.mixinsize
    self.carrybuf = Buf(np.empty(self.overflowsize, dtype = BufNode.floatdtype))
    self.f = Wave16(path, self.outrate)
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.out0 = 0 # Absolute index of first output sample being processed next iteration.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.chip = chip

  def callimpl(self):
    chipbuf = self.chain(self.chip)
    diffbuf = self.diffmaster.differentiate(self.dc, chipbuf)
    # Index of the first sample we can't output yet:
    outz = self.minbleps.getoutindexandshape(self.naivex + self.block.framecount)[0]
    outcount = outz - self.out0
    # Make space for all samples we can output plus overflow:
    outbuf = self.outmaster.ensureandcrop(outcount + self.overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:self.overflowsize] = self.carrybuf.buf
    outbuf.buf[self.overflowsize:] = self.dc
    nonzeros = diffbuf.nonzeros()
    outi, shape = self.minbleps.getoutindexandshape(self.naivex + nonzeros)
    outi -= self.out0
    mixin = self.minbleps.getmixin(shape, diffbuf.buf[nonzeros])
    amp = diffbuf.buf[nonzeros]
    pasteminbleps(len(nonzeros), outbuf.buf, outi, self.minbleps.mixinsize, mixin, amp)
    wavbuf = self.wavmaster.ensureandcrop(outcount)
    np.around(outbuf.buf[:outcount], out = wavbuf.buf)
    self.f.block(wavbuf)
    self.carrybuf.buf[:] = outbuf.buf[outcount:]
    self.naivex += self.block.framecount
    self.dc = chipbuf.buf[-1]
    self.out0 = outz

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()

# FIXME: This loop is too slow, so get numpy to implement it somehow.
def pasteminbleps(n, out, outi, mixinsize, mixin, amp):
  for x in xrange(n):
    i = outi[x]
    j = i + mixinsize
    m = mixin[x]
    out[i:j] += m
    out[j:] += amp[x]
