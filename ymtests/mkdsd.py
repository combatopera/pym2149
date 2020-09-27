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

from functools import reduce
import operator, sys

class Reg:

    def __init__(self, data, index, xform):
        self.data = data
        self.index = index
        self.xform = xform

    def put(self, *value):
        self.data.bytecode.extend([self.index, self.xform(*value)])

    def anim(self, preadjust, last):
        self.data.bytecode.extend([0x81, self.index, preadjust & 0xff, last])
        # If prev equals last we do a full cycle rather than nothing, see dosound0:
        value = self.data.prev
        while True:
            value = (value + preadjust) & 0xff
            self.data.totalticks += 1
            if value == last or value == self.data.prev:
                break

class UnsupportedTicksException(Exception): pass

class Data:

    def __init__(self):
        self.index = 0
        self.totalticks = 0
        self.bytecode = []

    def reg(self, xform = lambda x: x):
        r = Reg(self, self.index, xform)
        self.index += 1
        return r

    def setprev(self, prev):
        self.bytecode.extend([0x80, prev])
        self.prev = prev

    def sleep(self, ticks):
        if ticks < 2:
            raise UnsupportedTicksException(ticks)
        while ticks:
            part = min(256, ticks)
            self.bytecode.extend([0x82, part - 1])
            self.totalticks += part
            ticks -= part

    def save(self, f):
        w = lambda v: f.write(bytes(v))
        w([self.totalticks >> 8, self.totalticks & 0xff])
        w(self.bytecode)
        w([0x82, 0])

class Globals:

    def __init__(g, data):
        g.A_fine, g.A_rough, g.B_fine, g.B_rough, g.C_fine, g.C_rough, g.N_period = (data.reg() for _ in range(7))
        g.mixer = data.reg(lambda *v: 0x3f & ~reduce(operator.or_, v, 0))
        g.A_level, g.B_level, g.C_level, g.E_fine, g.E_rough, g.E_shape = (data.reg() for _ in range(6))
        g.A_tone, g.B_tone, g.C_tone, g.A_noise, g.B_noise, g.C_noise = (0x01 << i for i in range(6))
        g.setprev = data.setprev
        g.sleep = data.sleep

def main_mkdsd():
    for inpath in sys.argv[1:]:
        outpath = inpath[:inpath.rindex('.')] + '.dsd'
        print(outpath, file=sys.stderr)
        data = Data()
        exec(compile(open(inpath).read(), inpath, 'exec'), Globals(data).__dict__)
        with open(outpath, 'wb') as f:
            data.save(f)
