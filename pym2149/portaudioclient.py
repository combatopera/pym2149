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

from .iface import AmpScale, Config, Platform, Stream
from .jackclient import BufferFiller
from .nod import Node
from .out import FloatStream, StereoInfo
from .shapes import floatdtype
from diapyr import types
import logging, numpy as np

log = logging.getLogger(__name__)

class PortAudioClient(Platform):

    @types(Config, StereoInfo)
    def __init__(self, config, stereoinfo):
        config = config.PortAudio
        self.outputrate = config.outputrate # TODO: Find best rate supported by system.
        self.buffersize = config.buffersize
        self.chancount = stereoinfo.getoutchans.size
        self.port = self._newbuf(np.zeros) # Use zeros so initial underrun doesn't sound terrible.

    def _newbuf(self, constructor):
        return constructor(self.chancount * self.buffersize, dtype = floatdtype)

class PortAudioStream(Node, Stream, metaclass = AmpScale):

    log2maxpeaktopeak = 1

    @types(StereoInfo, FloatStream, PortAudioClient)
    def __init__(self, stereoinfo, wavs, client):
        super().__init__()
        self.chancount = stereoinfo.getoutchans.size
        self.wavs = wavs
        self.client = client

    def start(self):
        self.filler = BufferFiller(self.chancount, self.client.buffersize, self.client.current_output_buffer, self.client.send_and_get_output_buffer, True)
        self.client.activate()

    def callimpl(self):
        self.filler([self.chain(wav) for wav in self.wavs])

    def flush(self):
        pass

    def stop(self):
        self.client.deactivate()

def configure(di):
    di.add(PortAudioClient)
    di.add(PortAudioStream)
