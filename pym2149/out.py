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

import numpy as np, numba as nb, logging
from buf import MasterBuf, Buf
from minblep import MinBleps
from nod import Node, BufNode
from wav import Wave16
from mix import Multiplexer

log = logging.getLogger(__name__)

class WavWriter(Node):

  def __init__(self, wavs, path):
    Node.__init__(self)
    outrates = set(wav.outrate for wav in wavs)
    outrate, = outrates
    self.f = Wave16(path, outrate, len(wavs))
    try:
      self.data, = wavs
    except ValueError:
      self.data = Multiplexer(self.f.dtype, wavs)

  def callimpl(self):
    self.f.block(self.chain(self.data))

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()

class WavBuf(Node):

  outrate = 44100
  indexdtype = np.int32

  def __init__(self, clock, chip):
    Node.__init__(self)
    # XXX: Why does a tenth of ideal scale look better than ideal scale itself?
    scale = 1000 # Smaller values result in worse-looking spectrograms.
    self.diffmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.outmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.outimaster = MasterBuf(dtype = self.indexdtype)
    self.wavmaster = MasterBuf(dtype = Wave16.dtype)
    self.minbleps = MinBleps(clock, self.outrate, scale)
    # Need space for a whole mixin in case it is rooted at outz:
    self.overflowsize = self.minbleps.mixinsize
    self.carrybuf = Buf(np.empty(self.overflowsize, dtype = BufNode.floatdtype))
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.out0 = 0 # Absolute index of first output sample being processed next iteration.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.chip = chip

  def callimpl(self):
    # TODO: Unit-test that results do not depend on block size.
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
    pasten = self.indexdtype(len(nonzeros))
    outi, shape = self.minbleps.getoutindexandshape(self.naivex + nonzeros)
    outibuf = self.outimaster.ensureandcrop(pasten)
    np.subtract(outi, self.out0, outibuf.buf)
    amp = diffbuf.buf[nonzeros]
    pasteminbleps(pasten, outbuf.buf, outibuf.buf, self.indexdtype(len(outbuf)), self.indexdtype(self.minbleps.mixinsize), self.minbleps.minblep, shape, amp, self.indexdtype(self.minbleps.scale))
    wavbuf = self.wavmaster.ensureandcrop(outcount)
    np.around(outbuf.buf[:outcount], out = wavbuf.buf)
    self.carrybuf.buf[:] = outbuf.buf[outcount:]
    self.naivex += self.block.framecount
    self.dc = chipbuf.buf[-1]
    self.out0 = outz
    return wavbuf

def pasteminbleps(n, out, outi, outsize, mixinsize, minblep, shape, amp, scale):
  pasteminblepsimpl(n, out, outi, outsize, mixinsize, minblep, shape, amp, scale)

log.debug('Compiling output stage.')

@nb.jit(nb.void(nb.i4, nb.f4[:], nb.i4[:], nb.i4, nb.i4, nb.f4[:], nb.i4[:], nb.f4[:], nb.i4), nopython = True)
def pasteminblepsimpl(n, out, outi, outsize, mixinsize, minblep, shape, amp, scale):
  x = 0
  one = 1 # Makes inspect_types easier to read.
  while x < n:
    i = outi[x]
    s = shape[x]
    j = i + mixinsize
    a = amp[x]
    if i < j:
      while 1:
        out[i] += minblep[s] * a
        i += one
        s += scale
        if i == j:
          break
    if i < outsize:
      while 1:
        out[i] += a
        i += one
        if i == outsize:
          break
    x += one

log.debug('Done compiling.')
