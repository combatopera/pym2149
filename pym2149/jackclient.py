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

from nod import Node
from const import clientname
from iface import AmpScale
from out import FloatStream, StereoInfo
from iface import Stream, JackConnection, Config
from di import types
import native.cjack as cjack, logging

log = logging.getLogger(__name__)

class JackClient(JackConnection):

    @types(Config, StereoInfo)
    def __init__(self, config, stereoinfo):
        self.ringsize = config.jackringsize
        self.coupling = config.jackcoupling
        self.chancount = stereoinfo.getoutchans.size

    def start(self):
        self.jack = cjack.Client(clientname, self.chancount, self.ringsize, self.coupling)
        self.outputrate = self.jack.get_sample_rate() # defaultconf.py uses this.
        self.buffersize = self.jack.get_buffer_size()

    def port_register_output(self, port_name):
        self.jack.port_register_output(port_name)

    def activate(self):
        self.jack.activate()

    def connect(self, source_port_name, destination_port_name):
        self.jack.connect(source_port_name, destination_port_name)

    def current_output_buffer(self):
        return self.jack.current_output_buffer()

    def send_and_get_output_buffer(self):
        return self.jack.send_and_get_output_buffer()

    def deactivate(self):
        self.jack.deactivate()

    def stop(self):
        self.jack.dispose()

class JackStream(object, Node, Stream):

    __metaclass__ = AmpScale
    # For jack the available amplitude range is 2 ** 1:
    log2maxpeaktopeak = 1

    @types(Config, StereoInfo, FloatStream, JackClient)
    def __init__(self, config, stereoinfo, wavs, client):
        Node.__init__(self)
        self.systemchannelcount = config.systemchannelcount
        self.chancount = stereoinfo.getoutchans.size
        for chanindex in xrange(self.chancount):
            client.port_register_output("out_%s" % (1 + chanindex))
        self.wavs = wavs
        self.client = client

    def start(self):
        self.client.activate()
        # Connect all system channels, cycling over our streams if necessary:
        for syschanindex in xrange(self.systemchannelcount):
            chanindex = syschanindex % self.chancount
            self.client.connect("%s:out_%s" % (clientname, 1 + chanindex), "system:playback_%s" % (1 + syschanindex))
        self.outbuf = self.client.current_output_buffer()
        self.cursor = 0

    def getbuffersize(self):
        return self.client.buffersize

    def callimpl(self):
        outbufs = [self.chain(wav) for wav in self.wavs]
        n = len(outbufs[0])
        i = 0
        while i < n:
            m = min(n - i, self.client.buffersize - self.cursor)
            for chanindex in xrange(self.chancount):
                outbufs[chanindex].partcopyintonp(i, i + m, self.outbuf[chanindex, self.cursor:self.cursor + m])
            self.cursor += m
            i += m
            if self.cursor == self.client.buffersize:
                self.outbuf = self.client.send_and_get_output_buffer()
                self.cursor = 0

    def flush(self):
        pass # Nothing to be done.

    def stop(self):
        self.client.deactivate()

def configure(di):
    di.add(JackStream)
