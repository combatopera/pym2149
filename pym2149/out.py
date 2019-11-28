# Copyright 2014, 2018, 2019 Andrzej Cichocki

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

from .buf import MasterBuf
from .channels import Channels
from .clock import ClockInfo
from .iface import AmpScale, Multiplexed, Stream, Platform, Config
from .minblep import MinBleps
from .mix import IdealMixer, Multiplexer
from .nod import Node
from .shapes import floatdtype
from .wav import Wave16
from .ym2149 import YM2149
from diapyr import types
from diapyr.util import singleton
import numpy as np, logging

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
                self.maxpan = float(config.maxpan)
                self.getoutchans = self.getstaticoutchans
        else:
            self.getoutchans = self.gettrivialoutchans

    def pantoamp(self, outchan, pan):
        return ((1 + (outchan * 2 - 1) * pan) / 2) ** (self.panlaw / 6)

    def staticamp(self, outchan, chipchan):
        return self.pantoamp(outchan, (chipchan * 2 - (self.n - 1)) / (self.n - 1) * self.maxpan)

    def gettrivialoutchans(self, *args):
        return [TrivialOutChannel]
    gettrivialoutchans.size = 1

    def getstaticoutchans(self, *args):
        return [StaticOutChannel([self.staticamp(oc, cc) for cc in range(self.n)]) for oc in range(2)]
    getstaticoutchans.size = 2

    def getmidioutchans(self, channels):
        class PanToAmp:
            def __init__(this, outchan): this.outchan = outchan
            def __call__(this, pan): return self.pantoamp(this.outchan, pan)
        return [MidiOutChannel(channels, PanToAmp(outchan)) for outchan in range(2)]
    getmidioutchans.size = 2

class WavWriter(Stream, Node, metaclass = AmpScale):

    log2maxpeaktopeak = 16

    @types(Config, Multiplexed, StereoInfo, Platform)
    def __init__(self, config, wav, stereoinfo, platform):
        super().__init__()
        fclass = Wave16
        self.open = lambda: fclass(config.outpath, platform.outputrate, stereoinfo.getoutchans.size)
        self.roundmaster = MasterBuf(dtype = floatdtype)
        self.wavmaster = MasterBuf(dtype = fclass.dtype)
        self.wav = wav

    def start(self):
        self.f = self.open()

    def callimpl(self):
        outbuf = self.chain(self.wav)
        roundbuf = self.roundmaster.ensureandcrop(len(outbuf))
        wavbuf = self.wavmaster.ensureandcrop(len(outbuf))
        np.around(outbuf.buf, out = roundbuf.buf)
        wavbuf.buf[:] = roundbuf.buf
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

class MidiOutChannel(Node):

    nontrivial = True

    def __init__(self, channels, pantoamp):
        super().__init__()
        self.channels = channels
        self.pantoamp = pantoamp

    def size(self):
        return len(list(self.channels.getpans())) # Only called once.

    def callimpl(self):
        return [self.pantoamp(pan) for pan in self.channels.getpans()]

class FloatStream(list):

    @types(Config, ClockInfo, YM2149, AmpScale, StereoInfo, MinBleps, Channels)
    def __init__(self, config, clockinfo, chip, ampscale, stereoinfo, minbleps, channels = None):
        naives = [IdealMixer(chip, ampscale.log2maxpeaktopeak, outchan) for outchan in stereoinfo.getoutchans(channels)]
        for naive in naives:
            self.append(WavBuf(clockinfo, naive, minbleps))

class WavBuf(Node):

    @staticmethod
    @types(FloatStream, this = Multiplexed)
    def multi(wavs):
        if 1 == len(wavs):
            wav, = wavs
        else:
            wav = Multiplexer(floatdtype, wavs)
        return wav

    def __init__(self, clockinfo, naive, minbleps):
        super().__init__()
        self.diffmaster = MasterBuf(dtype = floatdtype)
        self.outmaster = MasterBuf(dtype = floatdtype)
        # Need space for a whole mixin in case it is rooted at sample outcount:
        self.overflowsize = minbleps.mixinsize
        self.carrybuf = MasterBuf(dtype = floatdtype).ensureandcrop(self.overflowsize)
        self.naivex = 0
        self.dc = floatdtype(0) # Last naive value of previous block.
        self.carrybuf.fill_same(self.dc) # Initial carry can be the initial dc level.
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

class WavPlatform(Platform):

    @types(Config)
    def __init__(self, config):
        self.outputrate = config.wavrate

def configure(di):
    di.add(WavPlatform)
    di.add(WavWriter)
    di.add(WavBuf.multi)
