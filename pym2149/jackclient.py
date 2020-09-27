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

from .const import clientname
from .iface import AmpScale, Config, Platform, Stream
from .nod import Node
from .out import FloatStream, StereoInfo
from diapyr import types
import outjack.jackclient as jc, logging

log = logging.getLogger(__name__)

class JackClient(jc.JackClient, Platform):

    @types(Config, StereoInfo)
    def __init__(self, config, stereoinfo):
        portcount = stereoinfo.getoutchans.size + config.SID.enabled # FIXME: This is a hack.
        super().__init__(clientname, portcount, config.jackringsize, config.jackcoupling)

    def start(self):
        super().start()
        log.debug(
            "JACK block size: %s or %.3f seconds",
            self.buffersize,
            self.buffersize / self.outputrate)

class JackStream(Stream, Node, metaclass = AmpScale):

    log2maxpeaktopeak = 1

    @types(Config, [FloatStream], JackClient)
    def __init__(self, config, streams, client):
        super().__init__()
        self.systemchannelcount = config.systemchannelcount
        for stream in streams:
            for chanindex in range(stream.chancount):
                client.port_register_output("%s_%s" % (stream.streamname, 1 + chanindex))
        self.streams = streams
        self.client = client

    def start(self):
        self.client.activate()
        for stream in self.streams:
            # Connect all system channels, cycling over our streams if necessary:
            for syschanindex in range(self.systemchannelcount):
                chanindex = syschanindex % stream.chancount
                self.client.connect("%s:%s_%s" % (clientname, stream.streamname, 1 + chanindex), "system:playback_%s" % (1 + syschanindex))
        self.filler = BufferFiller(sum(s.chancount for s in self.streams), self.client.buffersize, self.client.current_output_buffer, self.client.send_and_get_output_buffer)

    def callimpl(self):
        self.filler([self.chain(wav) for stream in self.streams for wav in stream])

    def flush(self):
        pass # Nothing to be done.

    def stop(self):
        self.client.deactivate()

class BufferFiller:

    def __init__(self, portcount, buffersize, init, flip, interleaved = False):
        self.portcount = portcount
        self.buffersize = buffersize
        self.interleaved = interleaved
        self._newbuf(init)
        self.flip = flip

    def __call__(self, outbufs):
        n = len(outbufs[0])
        i = 0
        while i < n:
            m = min(n - i, self.buffersize - self.cursor)
            for portindex in range(self.portcount):
                self.outbuf[portindex, self.cursor:self.cursor + m] = outbufs[portindex].buf[i:i + m]
            self.cursor += m
            i += m
            if self.cursor == self.buffersize:
                self._newbuf(self.flip)

    def _newbuf(self, factory):
        outbuf = factory().view()
        if self.interleaved:
            outbuf.shape = self.buffersize, self.portcount
            self.outbuf = outbuf.T
        else:
            outbuf.shape = self.portcount, self.buffersize
            self.outbuf = outbuf
        self.cursor = 0

def configure(di):
    di.add(JackClient)
    di.add(JackStream)
