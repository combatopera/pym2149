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

import numpy as np, logging, di
from buf import MasterBuf, Buf
from nod import Node, BufNode
from wav import Wave16
from mix import Multiplexer
from ym2149 import ClockInfo, YM2149
from util import AmpScale
from di import DI
from mix import IdealMixer
from minblep import MinBleps
from config import Config

log = logging.getLogger(__name__)

class WavWriter(object, Node):

  __metaclass__ = AmpScale
  log2maxpeaktopeak = 16

  def __init__(self, config, wav, channels, path):
    Node.__init__(self)
    self.f = Wave16(path, config.outputrate, channels)
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

  @staticmethod
  def multi(wavs):
    if 1 == len(wavs):
      wav, = wavs
    else:
      wav = Multiplexer(BufNode.floatdtype, wavs)
    return wav

  def __init__(self, clockinfo, naive, minbleps):
    Node.__init__(self)
    self.diffmaster = MasterBuf(dtype = BufNode.floatdtype)
    self.outmaster = MasterBuf(dtype = BufNode.floatdtype)
    # Need space for a whole mixin in case it is rooted at sample outcount:
    self.overflowsize = minbleps.mixinsize
    self.carrybuf = Buf(np.empty(self.overflowsize, dtype = BufNode.floatdtype))
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.naive = naive
    self.naiverate = clockinfo.implclock
    self.minbleps = minbleps

  def callimpl(self):
    # TODO: Unit-test that results do not depend on block size.
    naivebuf = self.chain(self.naive)
    diffbuf = self.diffmaster.differentiate(self.dc, naivebuf)
    outcount = self.minbleps.getoutcount(self.naivex, self.block.framecount)
    # Make space for all samples we can output plus overflow:
    outbuf = self.outmaster.ensureandcrop(outcount + self.overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:self.overflowsize] = self.carrybuf.buf
    outbuf.buf[self.overflowsize:] = self.dc
    self.minbleps.paste(self.naivex, diffbuf, outbuf)
    self.carrybuf.buf[:] = outbuf.buf[outcount:]
    self.naivex = (self.naivex + self.block.framecount) % self.naiverate
    self.dc = naivebuf.buf[-1]
    return Buf(outbuf.buf[:outcount])

class StereoInfo:

    def __init__(self, config):
        if config.stereo:
            n = config.chipchannels
            locs = (np.arange(n) * 2 - (n - 1)) / (n - 1) * config.maxpan
            def getamppair(loc):
                l = ((1 - loc) / 2) ** (config.panlaw / 6)
                r = ((1 + loc) / 2) ** (config.panlaw / 6)
                return l, r
            amppairs = [getamppair(loc) for loc in locs]
            self.chantoamps = zip(*amppairs)
        else:
            self.chantoamps = None

class FloatStream(list):

  @di.types(Config, ClockInfo, YM2149, AmpScale)
  def __init__(self, config, clockinfo, chip, ampscale):
    stereoinfo = StereoInfo(config)
    if stereoinfo.chantoamps is not None:
      naives = [IdealMixer(chip, ampscale.log2maxpeaktopeak, amps) for amps in stereoinfo.chantoamps]
    else:
      naives = [IdealMixer(chip, ampscale.log2maxpeaktopeak)]
    if config.outputrate != config.__getattr__('outputrate'):
      log.warn("Configured outputrate %s overriden to %s: %s", config.__getattr__('outputrate'), config.outputrateoverridelabel, config.outputrate)
    minbleps = MinBleps.loadorcreate(clockinfo.implclock, config.outputrate, None)
    for naive in naives:
      self.append(WavBuf(clockinfo, naive, minbleps))

def newchipandstream(config, outpath):
    di = DI()
    di.add(config)
    di.add(WavWriter)
    di.add(ClockInfo)
    di.add(YM2149)
    di.add(FloatStream)
    chip = di(YM2149)
    wavs = di(FloatStream)
    return chip, WavWriter(config, WavBuf.multi(wavs), len(wavs), outpath)
