# Copyright 2014, 2018 Andrzej Cichocki

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

class BadCommandException(Exception): pass

def dosound(bytecode, chip, timer, stream):
    def g():
        for b in bytecode:
            yield b & 0xff # It's supposed to be bytecode.
    g = g()
    def tick():
        for b in timer.blocksforperiod(50): # Authentic period.
            stream.call(b)
    while True:
        ctrl = next(g)
        if ctrl <= 0xF:
            chip.R[ctrl].value = next(g)
        elif 0x80 == ctrl:
            softreg = next(g)
        elif 0x81 == ctrl:
            targetreg = chip.R[next(g)]
            adjust = next(g)
            if adjust >= 0x80:
                adjust -= 0x100 # Convert back to signed.
            last = next(g)
            while True:
                softreg += adjust # Yes, this is done up-front.
                # The real thing simply uses the truncation on overflow:
                targetreg.value = softreg
                tick()
                # That's right, if we skip past it we loop forever:
                if last == softreg:
                    break
        elif ctrl >= 0x82:
            ticks = next(g)
            if not ticks:
                break
            ticks += 1 # Apparently!
            for _ in range(ticks):
                tick()
        else:
            raise BadCommandException(ctrl)
