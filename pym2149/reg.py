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
            self.reg.setimpl(self.xform(*upstreamvals))

class Reg(object):

    def __init__(self, **kwargs):
        self.links = []
        self.idle = True
        self.minval = kwargs.get('minval', None)
        self.maxval = kwargs.get('maxval', None)
        if 'value' in kwargs:
            self.value = kwargs['value']

    def link(self, xform, *upstream):
        link = Link(self, xform, upstream)
        for r in upstream:
            r.links.append(link)
        return self

    def mlink(self, mask, xform, *upstream):
        negmask = ~mask
        self.link(lambda *args: (negmask & self.value) | (mask & xform(*args)), *upstream)

    def __setattr__(self, name, value):
        if 'value' == name:
            self.set(value)
        else:
            object.__setattr__(self, name, value)

    def set(self, value):
        self.setimpl(value)

    def setimpl(self, value):
        if self.minval is not None:
            value = max(self.minval, value)
        if self.maxval is not None:
            value = min(self.maxval, value)
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'idle', False) # Significantly faster than going via __setattr__.
        try:
            for link in self.links:
                link.update()
        finally:
            object.__setattr__(self, 'idle', True)

class VersionReg(Reg):

    def __init__(self, **kwargs):
        self.version = 0
        super().__init__(**kwargs)

    def setimpl(self, value):
        super().setimpl(value)
        self.version += 1
