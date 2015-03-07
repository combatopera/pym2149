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

class Link:

    def __init__(self, reg, xform, upstream):
        self.reg = reg
        self.xform = xform
        self.upstream = upstream

    def update(self, done):
        if self.reg not in done:
            try:
                upstreamvals = [r.value for r in self.upstream]
            except AttributeError:
                return
            self.reg.setimpl(self.xform(*upstreamvals), done)

class Reg(object):

    def __init__(self):
        self.links = []
        self.done = set() # In the hope that clearing is cheaper than creating.

    def link(self, xform, *upstream):
        link = Link(self, xform, upstream)
        for r in upstream:
            r.links.append(link)

    def mlink(self, mask, xform, *upstream):
        negmask = ~mask
        self.link(lambda *args: (negmask & self.value) | (mask & xform(*args)), *upstream)

    def __setattr__(self, name, value):
        if 'value' == name:
            self.set(value)
        else:
            object.__setattr__(self, name, value)

    def set(self, value):
        try:
            self.setimpl(value, self.done)
        finally:
            self.done.clear()

    def setimpl(self, value, done):
        object.__setattr__(self, 'value', value)
        done.add(self)
        for link in self.links:
            link.update(done)

class VersionReg(Reg):

    def __init__(self):
        Reg.__init__(self)
        self.version = 0

    def setimpl(self, *args):
        Reg.setimpl(self, *args)
        self.version += 1
