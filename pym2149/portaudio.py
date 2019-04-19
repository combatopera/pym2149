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

from .iface import AmpScale, Platform, Stream
from .jackclient import BufferFiller
from .nod import Node
from .out import FloatStream, StereoInfo
from .shapes import floatdtype
from diapyr import types
from pyaudio import PyAudio, paFloat32
import numpy as np

class PortAudioClient(Platform):

    @types(StereoInfo)
    def __init__(self, stereoinfo):
        self.chancount = stereoinfo.getoutchans.size

    def start(self):
        self.p = PyAudio()
        self.outputrate = 44100 # TODO: Use native rate.
        self.buffersize = 1024 # TODO: Use native size.
        self.stream = self.p.open(
                rate = self.outputrate,
                channels = self.chancount,
                format = paFloat32,
                output = True,
                frames_per_buffer = self.buffersize)
        self.outbuf = np.empty(self.chancount * self.buffersize, dtype = floatdtype)

    def initial(self):
        return self.outbuf

    def flip(self):
        self.stream.write(self.outbuf, self.buffersize)
        return self.outbuf # TODO: Ring of these.

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

class PortAudioStream(Node, Stream, metaclass = AmpScale):

    log2maxpeaktopeak = 1

    @types(StereoInfo, FloatStream, PortAudioClient)
    def __init__(self, stereoinfo, wavs, client):
        super().__init__()
        self.chancount = stereoinfo.getoutchans.size
        self.wavs = wavs
        self.client = client

    def start(self):
        self.filler = BufferFiller(self.chancount, self.client.buffersize, self.client.initial, self.client.flip, True)

    def callimpl(self):
        self.filler([self.chain(wav) for wav in self.wavs])

    def flush(self):
        pass

    def stop(self):
        pass
