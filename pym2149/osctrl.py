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

import struct, io

bundlemagic = b'#bundle\0'
charset = 'ascii'
int32 = '>i'

def parse(v):
    return (Bundle.read if v.startswith(bundlemagic) else Message.read)(v)

class Reader:

    seconds1970 = 25567 * 24 * 60 * 60
    fractionlimit = 1 << 32

    def __init__(self, v):
        self.c = 0
        self.v = v

    def __bool__(self):
        return self.c < len(self.v)

    def consume(self, n):
        self.c += n
        return self.v[self.c - n:self.c]

    def align(self):
        self.c += (-self.c) % 4

    def int32(self):
        return struct.unpack(int32, self.consume(4))[0]

    def float32(self):
        return struct.unpack('>f', self.consume(4))[0]

    def float64(self):
        return struct.unpack('>d', self.consume(8))[0]

    def blob(self):
        blob = self.consume(self.int32())
        self.align()
        return blob

    def string(self):
        text = self.consume(self.v.index(b'\0', self.c) - self.c).decode(charset)
        self.c += 1 # Consume at least one null.
        self.align()
        return text

    def timetag(self):
        seconds1900, fraction = struct.unpack('>II', self.consume(8))
        return seconds1900 - self.seconds1970 + fraction / self.fractionlimit

    def element(self):
        return parse(self.consume(self.int32()))

class Writer:

    def __init__(self, f):
        self.f = f

    def s(self, text):
        v = text.encode(charset) + b'\0'
        v += b'\0' * ((-len(v)) % 4)
        self.f.write(v)

    def i(self, n):
        self.f.write(struct.pack(int32, n))

class Bundle:

    @classmethod
    def read(cls, v):
        return cls(v)

    def __init__(self, v):
        r = Reader(v)
        r.string()
        self.timetag = r.timetag()
        self.elements = []
        while r:
            self.elements.append(r.element())

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.timetag, self.elements)

class Message:

    types = {
        'i': Reader.int32,
        'f': Reader.float32,
        'd': Reader.float64,
        'b': Reader.blob,
        's': Reader.string,
    }
    tags = {
        int: 'i',
    }

    @classmethod
    def read(cls, v):
        r = Reader(v)
        return cls(r.string(), [cls.types[tt](r) for tt in r.string()[1:]])

    def __init__(self, addrpattern, args):
        self.addrpattern = addrpattern
        self.args = args

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.addrpattern, self.args)

    def ser(self):
        f = io.BytesIO()
        w = Writer(f)
        w.s(self.addrpattern)
        w.s(',' + ''.join(self.tags[type(arg)] for arg in self.args))
        for arg in self.args:
            getattr(w, self.tags[type(arg)])(arg)
        return f.getvalue()
