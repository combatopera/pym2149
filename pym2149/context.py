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

from .iface import Context, Config
from .lc import unit
from diapyr import types

class ContextImpl(Context):

    class Snapshot:

        @classmethod
        def create(cls, config):
            return cls(dict(
                __name__ = 'pym2149.context',
                tuning = config.tuning,
                mode = 1,
                speed = 16,
                sections = [[unit]],
            ))

        def __init__(self, data):
            self.cache = {}
            self.data = data

        def getattr(self, name):
            try:
                return self.data[name]
            except KeyError:
                raise AttributeError(name)

        def cached(self, name, factory):
            try:
                value = self.cache[name]
            except KeyError:
                self.cache[name] = value = factory()
            return value

        def fork(self, text):
            data = self.data.copy()
            exec(text, data) # XXX: Impact of modifying mutable objects?
            return type(self)(data), {name: obj for name, obj in data.items()
                    if name not in self.data or obj is not self.data[name]}

    @types(Config)
    def __init__(self, config):
        self._snapshot = self.Snapshot.create(config)

    def _update(self, text):
        self._snapshot, diff = self._snapshot.fork(text)
        return diff

    def __getattr__(self, name):
        return self._snapshot.getattr(name)

    def _cachedproperty(f):
        name = f.__name__
        def g(self):
            return self._snapshot.cached(name, lambda: f(self))
        return property(g)

    @_cachedproperty
    def sectionframecounts(self):
        return [self.speed * max(pattern.len for pattern in section) for section in self.sections]
