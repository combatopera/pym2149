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

class Link:

    def __init__(self, reg, xform, upstream):
        self.reg = reg
        self.xform = xform
        self.upstream = upstream

    def update(self):
        if self.reg.idle:
            try:
                upstreamvals = [r.value for r in self.upstream]
            except AttributeError:
                return
            self.reg.set(self.xform(*upstreamvals))

class Reg:

    undefined = object()

    def __init__(self, value = undefined, *, maxval = None, minval = None):
        self.links = []
        self.idle = True
        self.maxval = maxval # Friendlier than a mask.
        self.minval = minval # Typically to avoid 0 period.
        if value is not self.undefined:
            self.value = value

    def link(self, xform, *upstream):
        link = Link(self, xform, upstream)
        for r in upstream:
            r.links.append(link)
        return self

    def mlink(self, mask, xform, *upstream):
        negmask = ~mask
        self.link(lambda *args: (negmask & self.value) | (mask & xform(*args)), *upstream)

    def set(self, value):
        if self.maxval is not None:
            value = min(self.maxval, value)
        if self.minval is not None:
            value = max(self.minval, value)
        self._value = value
        self.idle = False
        try:
            for link in self.links:
                link.update()
        finally:
            self.idle = True

    value = property(lambda self: self._value, lambda self, value: self.set(value))

class VersionReg(Reg):

    version = 0

    def set(self, value):
        super().set(value)
        self.version += 1

def regproperty(reg):
    def fget(self):
        return reg(self).value
    def fset(self, value):
        reg(self).value = value
    return property(fget, fset)
