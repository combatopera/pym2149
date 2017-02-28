#!/usr/bin/env python3

import subprocess, sys, re, struct

command = ['sudo', 'tcpdump', '-Xl', '-i', 'lo', 'udp', 'dst', 'port', '57120']
lenpattern = re.compile(' length ([0-9]+)')
header = 28
linesize = 16
bytepattern = re.compile('[0-9a-f]{2}')
statusprefix = '/status\0'.encode('ascii')
bundleprefix = '#bundle\0'.encode('ascii')

def main():
    p = subprocess.Popen(command, stdout = subprocess.PIPE)
    readline = lambda: p.stdout.readline().decode()
    while True:
        line = readline()
        m = lenpattern.search(line)
        if m is None:
            continue
        n = int(m.group(1))
        total = header + n
        v = bytearray()
        for _ in range((total + linesize - 1) // linesize):
            line = readline()[10:49]
            v.extend(int(x, 16) for x in bytepattern.findall(line))
        del v[:header]
        obj = parse(v)
        if not obj.isstatus():
            obj.render()
            print()

def parse(v):
    return (Bundle if v.startswith(bundleprefix) else Message)(v)

def printable(b):
    b = chr(b)
    return b if b >= ' ' and b <= '~' else '.'

class Reader:

    seconds1970 = 25567 * 24 * 60 * 60
    fractionlimit = 1 << 32

    def __init__(self, v):
        self.c = 0
        self.v = v

    def consume(self, n):
        self.c += n
        return self.v[self.c - n:self.c]

    def timetag(self):
        seconds1900, fraction = struct.unpack('>II', self.consume(8))
        return seconds1900 - self.seconds1970 + fraction / self.fractionlimit

    def int32(self):
        return struct.unpack('>i', self.consume(4))[0]

    def __bool__(self):
        return self.c < len(self.v)

    def element(self):
        return parse(self.consume(self.int32()))

    def string(self):
        text = self.consume(self.v.index(b'\0', self.c) - self.c).decode('ascii')
        self.c += 1 # Consume at least one null.
        self.align()
        return text

    def align(self):
        while self.c % 4:
            self.c += 1

    def float32(self):
        return struct.unpack('>f', self.consume(4))[0]

    def float64(self):
        return struct.unpack('>d', self.consume(8))[0]

    def blob(self):
        blob = self.consume(self.int32())
        self.align()
        return blob

class Bundle:

    def __init__(self, v):
        r = Reader(v)
        r.string()
        self.timetag = r.timetag()
        self.elements = []
        while r:
            self.elements.append(r.element())

    def isstatus(self): return False

    def render(self):
        print(self.timetag)
        for e in self.elements:
            e.render()

class Message:

    def __init__(self, v):
        r = Reader(v)
        self.addrpattern = r.string()
        self.args = []
        for tt in r.string()[1:]:
            if 'i' == tt:
                a = r.int32()
            elif 's' == tt:
                a = r.string()
            elif 'f' == tt:
                a = r.float32()
            elif 'b' == tt:
                a = r.blob()
            elif 'd' == tt:
                a = r.float64()
            else:
                raise Exception("Unsupported Type Tag: %s" % tt)
            self.args.append(a)

    def isstatus(self): return '/status' == self.addrpattern

    def render(self):
        print(self.addrpattern, self.args)

if '__main__' == __name__:
    main()
