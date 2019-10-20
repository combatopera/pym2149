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
from diapyr import types

# TODO: Tests, refactor to enable global directive.
class ContextImpl(Context):

    class Snapshot:

        @classmethod
        def _create(cls, config):
            return cls(dict(
                __name__ = 'pym2149.context',
                tuning = config.tuning,
                mode = 1,
                speed = 16, # XXX: Needed when sections is empty?
                sections = (),
            ))

        def __init__(self, data):
            self._cache = {}
            self._data = data

        def _fork(self, text):
            data = self._data.copy()
            exec(text, data) # XXX: Impact of modifying mutable objects?
            return type(self)(data), {name: obj for name, obj in data.items()
                    if name not in self._data or obj is not self._data[name]}

        def _put(self, name, value):
            self._data[name] = value

        def __getattr__(self, name):
            try:
                return self._data[name]
            except KeyError:
                raise AttributeError(name)

        def _cachedproperty(f):
            name = f.__name__
            code = f.__code__
            params = code.co_varnames[1:code.co_argcount]
            def g(self):
                args = [getattr(self, p) for p in params]
                try:
                    cacheargs, value = self._cache[name]
                    if all(x is y for x, y in zip(cacheargs, args)):
                        return value
                except KeyError:
                    pass
                value = f(*[self] + args)
                self._cache[name] = args, value
                return value
            return property(g)

        @_cachedproperty
        def sectionframecounts(self, speed, sections):
            return [speed * max(pattern.len for pattern in section) for section in sections]

        @_cachedproperty
        def totalframecount(self, sectionframecounts):
            return sum(sectionframecounts)

    @types(Config)
    def __init__(self, config):
        self._pending = self.Snapshot._create(config)
        self._flip()

    def _update(self, text, flip):
        self._pending, diff = self._pending._fork(text)
        if flip:
            self._flip()
        return diff

    def _flip(self):
        self._snapshot = self._pending

    def __getattr__(self, name):
        return getattr(self._snapshot, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._snapshot._put(name, value)
