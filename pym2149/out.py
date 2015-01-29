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
import numpy as np, logging
from buf import MasterBuf, Buf
from nod import Node, BufNode
from wav import Wave16
from mix import Multiplexer
from ym2149 import ClockInfo, YM2149
from util import AmpScale
from di import DI, types
from mix import IdealMixer
from minblep import MinBleps
from config import Config

log = logging.getLogger(__name__)

class WavWriter(object, Node):

  __metaclass__ = AmpScale
  log2maxpeaktopeak = 16

  def __init__(self, config, wav, stereoinfo, path):
    Node.__init__(self)
    self.f = Wave16(path, config.outputrate, len(stereoinfo.outchans))
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

class OutChannel:

    def __init__(self, chipamps):
        self.chipamps = chipamps

class StereoInfo:

    @types(Config)
    def __init__(self, config):
        n = config.chipchannels
        if config.stereo:
            locs = (np.arange(n) * 2 - (n - 1)) / (n - 1) * config.maxpan
            def getamppair(loc):
                l = ((1 - loc) / 2) ** (config.panlaw / 6)
                r = ((1 + loc) / 2) ** (config.panlaw / 6)
                return l, r
            amppairs = [getamppair(loc) for loc in locs]
            outchan2chipamps = zip(*amppairs)
        else:
            outchan2chipamps = [[1] * n]
        self.outchans = [OutChannel(amps) for amps in outchan2chipamps]

class FloatStream(list):

  @types(Config, ClockInfo, YM2149, AmpScale, StereoInfo)
  def __init__(self, config, clockinfo, chip, ampscale, stereoinfo):
    naives = [IdealMixer(chip, ampscale.log2maxpeaktopeak, outchan.chipamps) for outchan in stereoinfo.outchans]
    if config.outputrate != config.__getattr__('outputrate'):
      log.warn("Configured outputrate %s overriden to %s: %s", config.__getattr__('outputrate'), config.outputrateoverridelabel, config.outputrate)
    minbleps = MinBleps.loadorcreate(clockinfo.implclock, config.outputrate, None)
    for naive in naives:
      self.append(WavBuf(clockinfo, naive, minbleps))

class Multiplexed: pass

class WavBuf(Node):

  @staticmethod
  @types(FloatStream, this = Multiplexed)
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

def newchipandstream(config, outpath):
    di = DI()
    di.add(config)
    di.addinstance(WavWriter)
    di.add(ClockInfo)
    di.add(YM2149)
    di.add(StereoInfo)
    di.add(FloatStream)
    di.add(WavBuf.multi)
    @types(Config, Multiplexed, StereoInfo, this = WavWriter)
    def writerfactory(config, writable, stereoinfo):
        return WavWriter(config, writable, stereoinfo, outpath)
    di.add(writerfactory)
    return di(YM2149), di(WavWriter)
