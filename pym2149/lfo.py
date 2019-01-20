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

from decimal import Decimal, ROUND_HALF_DOWN, ROUND_HALF_UP

class AbstractLFO:

    def __init__(self, initial):
        self.v = [initial]
        self.looplenornone = 1

    def lin(self, n, target):
        source = self.v[-1]
        for i in range(1, n + 1):
            self.v.append(source + (target - source) * i / n)
        return self

    def jump(self, target):
        self.v[-1] = target
        return self

    def then(self, *vals):
        self.v.extend(vals)
        return self

    def hold(self, n):
        for _ in range(n):
            self.v.append(self.v[-1])
        return self

    def tri(self, trin, linn, target):
        if 0 != trin % 4:
            raise Exception("Expected a multiple of 4 but got: %s" % trin)
        normn = trin // 4
        if 0 != normn % linn:
            raise Exception("Expected a factor of %s but got: %s" % (normn, linn))
        source = self.v[-1]
        for _ in range(normn // linn):
            self.lin(linn, target)
            self.lin(linn * 2, source * 2 - target)
            self.lin(linn, source)
        return self

    def loop(self, n = None):
        self.looplenornone = n
        return self

    def get(self, frame):
        n = len(self.v)
        if frame >= n:
            looplen = n if self.looplenornone is None else self.looplenornone
            start = n - looplen
            frame = start + ((frame - start) % looplen)
        return self.v[frame]

    def render(self, n = None):
        if n is None:
            n = len(self.v)
        return [self(i) for i in range(n)] # Observe via the xform.

class LFO(AbstractLFO):

    def __call__(self, frame):
        current, next = self.get(frame), self.get(frame + 1)
        if current < 0:
            towards0 = (current < next) if (next < 0) else True
        else:
            towards0 = True if (next < 0) else (next < current)
        rounding = ROUND_HALF_DOWN if towards0 else ROUND_HALF_UP
        return int(Decimal(current).to_integral_value(rounding))

class FloatLFO(AbstractLFO):

    def __call__(self, frame):
        return self.get(frame)
