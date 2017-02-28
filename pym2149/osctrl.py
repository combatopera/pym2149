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
import struct

bundlemagic = '#bundle\0'

def parse(v):
    return (Bundle if v.startswith(bundlemagic) else Message)(v)

class Reader:

    seconds1970 = 25567 * 24 * 60 * 60
    fractionlimit = 1 << 32

    def __init__(self, v):
        self.c = 0
        self.v = v

    def __nonzero__(self):
        return self.c < len(self.v)

    def consume(self, n):
        self.c += n
        return self.v[self.c - n:self.c]

    def align(self):
        self.c += (-self.c) % 4

    def int32(self):
        return struct.unpack('>i', self.consume(4))[0]

    def float32(self):
        return struct.unpack('>f', self.consume(4))[0]

    def float64(self):
        return struct.unpack('>d', self.consume(8))[0]

    def blob(self):
        blob = self.consume(self.int32())
        self.align()
        return blob

    def string(self):
        text = self.consume(self.v.index('\0', self.c) - self.c).decode('ascii')
        self.c += 1 # Consume at least one null.
        self.align()
        return text

    def timetag(self):
        seconds1900, fraction = struct.unpack('>II', self.consume(8))
        return seconds1900 - self.seconds1970 + fraction / self.fractionlimit

    def element(self):
        return parse(self.consume(self.int32()))

class Bundle:

    def __init__(self, v):
        r = Reader(v)
        r.string()
        self.timetag = r.timetag()
        self.elements = []
        while r:
            self.elements.append(r.element())

class Message:

    types = {
        'i': Reader.int32,
        'f': Reader.float32,
        'd': Reader.float64,
        'b': Reader.blob,
        's': Reader.string,
    }

    def __init__(self, v):
        r = Reader(v)
        self.addrpattern = r.string()
        self.args = []
        for tt in r.string()[1:]:
            self.args.append(self.types[tt](r))
