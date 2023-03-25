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

octet = 8

class Stream:

    masks = [(1 << m) - 1 for m in range(octet + 1)] # Element 0 unused.
    remaining = octet

    def __init__(self, data, cursor = 0, step = 1):
        self.data = data
        self.cursor = cursor
        self.step = step

    def read(self, n):
        x = 0
        while n:
            m = min(n, self.remaining)
            n -= m
            self.remaining -= m
            x = x << m | self.data[self.cursor] >> self.remaining & self.masks[m]
            if not self.remaining:
                self.cursor += self.step
                self.remaining = octet
        return x

    def readcodelen(self):
        x = self.read(3)
        if 7 == x:
            while self.read(1):
                x += 1
        return x

class Tree:

    trivialkey = 1 # The empty code prefixed with a 1.

    @classmethod
    def canonical(cls, codelens):
        lookup = {}
        key = cls.trivialkey
        currentlen = 0
        for l, value in sorted((l, x) for x, l in enumerate(codelens) if l):
            key <<= l - currentlen
            currentlen = l
            lookup[key] = value
            key += 1
        return cls(lookup)

    @classmethod
    def degenerate(cls, value):
        return cls({cls.trivialkey: value})

    def __init__(self, lookup):
        self.lookup = lookup

    def readvalue(self, stream):
        k = self.trivialkey
        while k not in self.lookup:
            k = k << 1 | stream.read(1)
        return self.lookup[k]

class UnsupportedFormatException(Exception): pass

class Interpreter(Tree):

    @classmethod
    def readtree(cls, stream, prefix = 3):
        size = stream.read(5)
        if not size:
            return cls.degenerate(stream.read(5))
        if prefix < size:
            lens = [stream.readcodelen() for _ in range(prefix)]
            zeros = stream.read(2) # XXX: When prefix == size should this be done redundantly?
            lens.extend(0 for _ in range(zeros))
            lens.extend(stream.readcodelen() for _ in range(size - prefix - zeros))
        else:
            lens = [stream.readcodelen() for _ in range(size)]
        return cls.canonical(lens)

    def mainlens(self, stream, lookup = {
        0: lambda s: 1,
        1: lambda s: 3 + s.read(4),
        2: lambda s: 20 + s.read(9),
    }):
        instruction = self.readvalue(stream)
        readzeros = lookup.get(instruction)
        if readzeros is None:
            yield instruction - 2
        else:
            for _ in range(readzeros(stream)):
                yield 0

class Main(Tree):

    @classmethod
    def readtree(cls, stream):
        interpreter = Interpreter.readtree(stream)
        size = stream.read(9)
        if not size:
            return cls.degenerate(stream.read(9))
        lens = []
        while len(lens) < size:
            lens.extend(interpreter.mainlens(stream))
        return cls.canonical(lens)

    def invoke(self, pair, offset):
        x = self.readvalue(pair.stream)
        if x < 256:
            yield x
        else:
            yield from offset.copy(pair, x - 253)

class Offset(Tree):

    @classmethod
    def readtree(cls, stream):
        size = stream.read(4)
        if not size:
            return cls.degenerate(stream.read(4))
        return cls.canonical(stream.readcodelen() for _ in range(size))

    def copy(self, pair, n):
        off = len(pair.buffer) - 1
        x = self.readvalue(pair.stream)
        if x < 2:
            off -= x
        else:
            x -= 1
            off -= (1 << x) | pair.stream.read(x)
        for i in range(off, off + n):
            yield pair.buffer[i]

class Pair:

    def __init__(self, stream):
        self.buffer = []
        self.stream = stream

    def pipe(self, targetlen):
        while len(self.buffer) != targetlen:
            commands = self.stream.read(16)
            main = Main.readtree(self.stream)
            offset = Offset.readtree(self.stream)
            for _ in range(commands):
                self.buffer.extend(main.invoke(self, offset))

def unlha(u):
    if b'-lh5-' != u[2:7] or u[20]:
        raise UnsupportedFormatException
    encstart = 2 + u[0]
    afterenc = encstart + Stream(u, 10, -1).read(32)
    if afterenc != len(u) - 1 or u[afterenc]:
        raise UnsupportedFormatException
    pair = Pair(Stream(u, encstart))
    pair.pipe(Stream(u, 14, -1).read(32))
    return bytes(pair.buffer)
