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

import numpy as np, logging
from buf import MasterBuf, Buf
from minblep import MinBleps
from nod import Node, BufNode
from wav import Wave16
from mix import Multiplexer

log = logging.getLogger(__name__)

class WavWriter(Node):

  def __init__(self, wav, path):
    Node.__init__(self)
    self.f = Wave16(path, wav.outrate, wav.channels)
    self.wavmaster = MasterBuf(dtype = self.f.dtype)
    self.wav = wav

  def callimpl(self):
    outbuf = self.chain(self.wav)
    wavbuf = self.wavmaster.ensureandcrop(len(outbuf))
    np.around(outbuf.buf, out = wavbuf.buf)
    self.f.block(wavbuf)

  def flush(self):
    self.f.flush()

  def close(self):
    self.f.close()

class WavBuf(Node):

  indexdtype = np.int32

  @staticmethod
  def multi(wavs):
    channels = len(wavs)
    if 1 == channels:
      wav, = wavs
    else:
      wav = Multiplexer(BufNode.floatdtype, wavs)
      wav.outrate = wavs[0].outrate
    wav.channels = channels
    return wav

  def __init__(self, clock, naive, outrate):
    Node.__init__(self)
    # XXX: Why does a tenth of ideal scale look better than ideal scale itself?
    scale = 1000 # Smaller values result in worse-looking spectrograms.
    self.diffmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.outmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.outimaster = MasterBuf(dtype = self.indexdtype)
    self.shapemaster = MasterBuf(dtype = self.indexdtype)
    self.minbleps = MinBleps(clock, outrate, scale)
    # Need space for a whole mixin in case it is rooted at outz:
    self.overflowsize = self.minbleps.mixinsize
    self.carrybuf = Buf(np.empty(self.overflowsize, dtype = BufNode.floatdtype))
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.out0 = 0 # Absolute index of first output sample being processed next iteration.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.naive = naive
    self.outrate = outrate

  def callimpl(self):
    # TODO: Unit-test that results do not depend on block size.
    chipbuf = self.chain(self.naive)
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
    self.minbleps.paste(self.naivex + nonzeros, self.out0, diffbuf.buf[nonzeros], self.outimaster, self.shapemaster, outbuf)
    self.carrybuf.buf[:] = outbuf.buf[outcount:]
    self.naivex += self.block.framecount
    self.dc = chipbuf.buf[-1]
    self.out0 = outz
    return Buf(outbuf.buf[:outcount])
