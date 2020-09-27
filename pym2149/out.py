# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .buf import BufType
from .clock import ClockInfo
from .iface import AmpScale, Config, Multiplexed, Platform, Stream
from .minblep import MinBleps
from .mix import IdealMixer, Multiplexer
from .nod import Node
from .shapes import floatdtype
from .wav import Wave16
from .ym2149 import YM2149
from diapyr import types
from diapyr.util import singleton
import logging, numpy as np

log = logging.getLogger(__name__)

class StereoInfo:

    @types(Config)
    def __init__(self, config):
        self.n = config.chipchannels
        if config.stereo:
            self.panlaw = config.panlaw
            self.maxpan = float(config.maxpan)
            self.getoutchans = self.getstaticoutchans
        else:
            self.getoutchans = self.gettrivialoutchans

    def pantoamp(self, outchan, pan):
        return ((1 + (outchan * 2 - 1) * pan) / 2) ** (self.panlaw / 6)

    def staticamp(self, outchan, chipchan):
        return self.pantoamp(outchan, (chipchan * 2 - (self.n - 1)) / (self.n - 1) * self.maxpan)

    def gettrivialoutchans(self):
        return [TrivialOutChannel]
    gettrivialoutchans.size = 1

    def getstaticoutchans(self):
        return [StaticOutChannel([self.staticamp(oc, cc) for cc in range(self.n)]) for oc in range(2)]
    getstaticoutchans.size = 2

class WavWriter(Stream, Node, metaclass = AmpScale):

    log2maxpeaktopeak = 16

    @types(Config, Multiplexed, StereoInfo, Platform)
    def __init__(self, config, wav, stereoinfo, platform):
        super().__init__()
        fclass = Wave16
        self.open = lambda: fclass(config.outpath, platform.outputrate, stereoinfo.getoutchans.size)
        self.roundmaster = BufType.float()
        self.wavmaster = fclass.buftype()
        self.wav = wav

    def start(self):
        self.f = self.open()

    def callimpl(self):
        outbuf = self.chain(self.wav)
        roundbuf = self.roundmaster.ensureandcrop(len(outbuf))
        wavbuf = self.wavmaster.ensureandcrop(len(outbuf))
        np.around(outbuf.buf, out = roundbuf.buf)
        wavbuf.copybuf(roundbuf)
        self.f.block(wavbuf)

    def flush(self):
        self.f.flush()

    def stop(self):
        self.f.close()

class StaticOutChannel(Node):

    nontrivial = True

    def __init__(self, chipamps):
        super().__init__()
        self.chipamps = chipamps

    def size(self):
        return len(self.chipamps)

    def callimpl(self):
        return self.chipamps

@singleton
class TrivialOutChannel:

    nontrivial = False

class FloatStream(list):

    chancount = property(len)

class YMStream(FloatStream):

    streamname = 'ym'

    @types(Config, ClockInfo, YM2149, AmpScale, StereoInfo, MinBleps)
    def __init__(self, config, clockinfo, chip, ampscale, stereoinfo, minbleps):
        naives = [IdealMixer(chip, ampscale.log2maxpeaktopeak, outchan) for outchan in stereoinfo.getoutchans()]
        for naive in naives:
            self.append(WavBuf(clockinfo, naive, minbleps))

class Translator: # TODO: Convert to Node.

    naivex = 0

    def __init__(self, clockinfo, minbleps):
        self.naiverate = clockinfo.implclock
        self.minbleps = minbleps

    def step(self, framecount):
        naivex = self.naivex
        outcount = self.minbleps.getoutcount(naivex, framecount)
        self.naivex = (naivex + framecount) % self.naiverate
        return naivex, outcount

class WavBuf(Node):

    @staticmethod
    @types(FloatStream, this = Multiplexed)
    def multi(wavs):
        if 1 == len(wavs):
            wav, = wavs
        else:
            wav = Multiplexer(BufType.float, wavs)
        return wav

    def __init__(self, clockinfo, naive, minbleps):
        super().__init__()
        self.diffmaster = BufType.float()
        self.outmaster = BufType.float()
        # Need space for a whole mixin in case it is rooted at sample outcount:
        self.overflowsize = minbleps.mixinsize
        self.carrybuf = BufType.float().ensureandcrop(self.overflowsize)
        self.translator = Translator(clockinfo, minbleps)
        self.dc = floatdtype(0) # Last naive value of previous block.
        self.carrybuf.fill_same(self.dc) # Initial carry can be the initial dc level.
        self.naive = naive
        self.minbleps = minbleps

    def callimpl(self):
        # TODO: Unit-test that results do not depend on block size.
        naivebuf = self.chain(self.naive)
        diffbuf = self.diffmaster.ensureandcrop(len(naivebuf))
        diffbuf.differentiate(self.dc, naivebuf)
        naivex, outcount = self.translator.step(self.block.framecount)
        # Make space for all samples we can output plus overflow:
        outsize = outcount + self.overflowsize
        outbuf = self.outmaster.ensureandcrop(outsize)
        # Paste in the carry followed by the carried dc level:
        outbuf.copyasprefix(self.overflowsize, self.carrybuf)
        outbuf.fillpart(self.overflowsize, outsize, self.dc)
        self.minbleps.paste(naivex, diffbuf, outbuf)
        self.carrybuf.copywindow(outbuf, outcount, outsize)
        self.dc = naivebuf.last()
        return self.outmaster.ensureandcrop(outcount)

class WavPlatform(Platform):

    @types(Config)
    def __init__(self, config):
        self.outputrate = config.wavrate

def configure(di):
    di.add(WavPlatform)
    di.add(WavWriter)
    di.add(WavBuf.multi)
