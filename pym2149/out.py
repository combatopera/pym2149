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
from buf import MasterBuf
from nod import Node, BufNode
from wav import Wave16
from mix import Multiplexer
from ym2149 import ClockInfo, YM2149
from iface import AmpScale, Multiplexed, Stream, JackConnection, Config
from di import types
from mix import IdealMixer
from minblep import MinBleps
from channels import Channels

log = logging.getLogger(__name__)

class StereoInfo:

    @types(Config)
    def __init__(self, config):
        self.n = config.chipchannels
        if config.stereo:
            self.panlaw = config.panlaw
            if config.midipan:
                self.getoutchans = self.getmidioutchans
            else:
                self.maxpan = config.maxpan
                self.getoutchans = self.getstaticoutchans
        else:
            self.getoutchans = self.gettrivialoutchans

    def pantoamp(self, outchan, pan):
        return ((1 + (outchan * 2 - 1) * pan) / 2) ** (self.panlaw / 6)

    def staticamp(self, outchan, chipchan):
        return self.pantoamp(outchan, (chipchan * 2 - (self.n - 1)) / (self.n - 1) * self.maxpan)

    def gettrivialoutchans(self, *args):
        return [TrivialOutChannel(self.n)]
    gettrivialoutchans.size = 1

    def getstaticoutchans(self, *args):
        return [StaticOutChannel([self.staticamp(oc, cc) for cc in xrange(self.n)]) for oc in xrange(2)]
    getstaticoutchans.size = 2

    def getmidioutchans(self, channels):
        class PanToAmp:
            def __init__(this, outchan): this.outchan = outchan
            def __call__(this, pan): return self.pantoamp(this.outchan, pan)
        return [MidiOutChannel(channels, PanToAmp(outchan)) for outchan in xrange(2)]
    getmidioutchans.size = 2

class WavWriter(object, Node, Stream):

  __metaclass__ = AmpScale
  log2maxpeaktopeak = 16

  @types(Config, Multiplexed, StereoInfo)
  def __init__(self, config, wav, stereoinfo):
    Node.__init__(self)
    fclass = Wave16
    self.open = lambda: fclass(config.outpath, config.outputrate, stereoinfo.getoutchans.size)
    self.wavmaster = MasterBuf(dtype = fclass.dtype)
    self.wav = wav

  def start(self):
    self.f = self.open()

  def callimpl(self):
    outbuf = self.chain(self.wav)
    wavbuf = self.wavmaster.ensureandcrop(len(outbuf))
    np.around(outbuf.buf, out = wavbuf.buf)
    self.f.block(wavbuf)

  def flush(self):
    self.f.flush()

  def stop(self):
    self.f.close()

class StaticOutChannel(Node):

    nontrivial = True

    def __init__(self, chipamps):
        Node.__init__(self)
        self.chipamps = chipamps

    def size(self):
        return len(self.chipamps)

    def callimpl(self):
        return self.chipamps

class TrivialOutChannel(StaticOutChannel):

    nontrivial = False

    def __init__(self, n):
        StaticOutChannel.__init__(self, [1] * n)

class MidiOutChannel(Node):

    nontrivial = True

    def __init__(self, channels, pantoamp):
        Node.__init__(self)
        self.channels = channels
        self.pantoamp = pantoamp

    def size(self):
        return len(list(self.channels.getpans())) # Only called once.

    def callimpl(self):
        return [self.pantoamp(pan) for pan in self.channels.getpans()]

class FloatStream(list):

  @types(Config, ClockInfo, YM2149, AmpScale, StereoInfo, MinBleps, JackConnection, Channels)
  def __init__(self, config, clockinfo, chip, ampscale, stereoinfo, minbleps, jackconn = None, channels = None):
    naives = [IdealMixer(chip, ampscale.log2maxpeaktopeak, outchan) for outchan in stereoinfo.getoutchans(channels)]
    if jackconn is not None and config.outputrate != jackconn.outputrate:
      log.info("Context outputrate %s overriden to: %s", jackconn.outputrate, config.outputrate)
    for naive in naives:
      self.append(WavBuf(clockinfo, naive, minbleps))

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
    self.carrybuf = MasterBuf(dtype = BufNode.floatdtype).ensureandcrop(self.overflowsize)
    self.naivex = 0
    self.dc = 0 # Last naive value of previous block.
    self.carrybuf.fill(self.dc) # Initial carry can be the initial dc level.
    self.naive = naive
    self.naiverate = clockinfo.implclock
    self.minbleps = minbleps

  def callimpl(self):
    # TODO: Unit-test that results do not depend on block size.
    naivebuf = self.chain(self.naive)
    diffbuf = self.diffmaster.ensureandcrop(len(naivebuf))
    diffbuf.differentiate(self.dc, naivebuf)
    outcount = self.minbleps.getoutcount(self.naivex, self.block.framecount)
    # Make space for all samples we can output plus overflow:
    outsize = outcount + self.overflowsize
    outbuf = self.outmaster.ensureandcrop(outsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.copyasprefix(self.overflowsize, self.carrybuf)
    outbuf.fillpart(self.overflowsize, outsize, self.dc)
    self.minbleps.paste(self.naivex, diffbuf, outbuf)
    self.carrybuf.copywindow(outbuf, outcount, outsize)
    self.naivex = (self.naivex + self.block.framecount) % self.naiverate
    self.dc = naivebuf.last()
    return self.outmaster.ensureandcrop(outcount)

def configure(di):
    di.add(WavWriter)
    di.add(WavBuf.multi)
