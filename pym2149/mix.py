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
from .nod import BufNode, Node
import logging

log = logging.getLogger(__name__)

class BinMix(BufNode):

    def __init__(self, tone, noise, toneflagreg, noiseflagreg):
        super().__init__(BufType.signal)
        self.tone = tone
        self.noise = noise
        self.toneflagreg = toneflagreg
        self.noiseflagreg = noiseflagreg

    def callimpl(self):
        # The truth table options are {AND, OR, XOR}.
        # Other functions are negations of these, the 2 constants, or not symmetric.
        # XOR sounds just like noise so it can't be that.
        # AND and OR have the same frequency spectrum so either will sound good.
        # We use AND as zero is preferred over envelope, see qbmixenv:
        noiseflag = self.noiseflagreg.value
        if self.toneflagreg.value:
            self.blockbuf.copybuf(self.chain(self.tone))
            if noiseflag:
                self.blockbuf.andbuf(self.chain(self.noise))
        elif noiseflag:
            self.blockbuf.copybuf(self.chain(self.noise))
        else:
            # Fixed and variable levels should work, see qanlgmix and qenvpbuf:
            self.blockbuf.fill_i1(1)

class Multiplexer(Node):

    def __init__(self, buftype, streams):
        super().__init__()
        self.multi = buftype()
        self.channels = len(streams)
        self.streams = streams

    def callimpl(self):
        for i, stream in enumerate(self.streams):
            buf = self.chain(stream)
            if not i:
                # BufNode can't do this because size is not framecount:
                size = len(buf)
                multi = self.multi.ensureandcrop(size * self.channels)
            multi.putstrided(i, i + self.channels * size, self.channels, buf.buf)
        return multi

class IdealMixer(BufNode):

    def __init__(self, container, log2maxpeaktopeak, chipamps):
        log.debug("Mix is trivial: %s", not chipamps.nontrivial)
        buftype = BufType.float
        if chipamps.nontrivial:
            if len(container) != chipamps.size():
                raise Exception("Expected %s chipamps but got: %s" % (len(container), chipamps.size()))
            self.contrib = buftype()
            self.callimpl = self.nontrivialcallimpl
        else:
            self.callimpl = self.trivialcallimpl
        super().__init__(buftype)
        self.datum = buftype.dtype(2 ** (log2maxpeaktopeak - 1.5)) # Half power point, very close to -3 dB.
        self.container = container
        self.chipamps = chipamps

    def nontrivialcallimpl(self):
        self.blockbuf.fill_same(self.datum)
        contrib = self.contrib.ensureandcrop(self.block.framecount)
        for buf, amp in zip(self.chain(self.container), self.chain(self.chipamps)):
            if amp:
                contrib.copybuf(buf)
                contrib.mul(amp)
                self.blockbuf.subbuf(contrib)

    def trivialcallimpl(self):
        self.blockbuf.fill_same(self.datum)
        for buf in self.chain(self.container):
            self.blockbuf.subbuf(buf)
