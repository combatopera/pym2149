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
import errno, struct, sys

class Wave16:

    bytespersample = 2
    hugefilesize = 0x80000000
    buftype = BufType.int16
    formats = {2: '<H', 4: '<I'}

    def __init__(self, path, rate, channels):
        if '-' == path:
            self.f = sys.stdout.buffer
        else:
            self.f = open(path, 'wb') # Binary.
        self.f.write(b'RIFF')
        self.riffsizeoff = 4
        self.writeriffsize(self.hugefilesize)
        self.f.write(b'WAVEfmt ') # Observe trailing space.
        self.writen(16) # Chunk data size.
        self.writen(1, 2) # PCM (uncompressed).
        self.writen(channels, 2)
        self.writen(rate)
        bytesperframe = self.bytespersample * channels
        self.writen(rate * bytesperframe) # Bytes per second.
        self.writen(bytesperframe, 2)
        self.writen(self.bytespersample * 8, 2) # Bits per sample.
        self.f.write(b'data')
        self.datasizeoff = 40
        self.writedatasize(self.hugefilesize)
        self.adjustsizes()

    def writeriffsize(self, filesize):
        self.writen(filesize - (self.riffsizeoff + 4))

    def writedatasize(self, filesize):
        self.writen(filesize - (self.datasizeoff + 4))

    def writen(self, n, size = 4):
        self.f.write(struct.pack(self.formats[size], n))

    def block(self, buf):
        buf.tofile(self.f)
        self.adjustsizes()

    def adjustsizes(self):
        try:
            filesize = self.f.tell()
            if not filesize:
                return # It's probably /dev/null so give up.
        except IOError as e:
            if errno.ESPIPE != e.errno:
                raise
            return # Leave huge sizes.
        self.f.seek(self.riffsizeoff)
        self.writeriffsize(filesize)
        self.f.seek(self.datasizeoff)
        self.writedatasize(filesize)
        self.f.seek(filesize)

    def flush(self):
        self.f.flush()

    def close(self):
        self.f.close()
