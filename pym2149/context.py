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
import logging

log = logging.getLogger(__name__)

class ContextImpl(Context):

    deleted = object()

    @types(Config)
    def __init__(self, config):
        self._globals = dict(
            __name__ = 'pym2149.context',
            tuning = config.tuning,
            mode = 1,
            speed = 16, # XXX: Needed when sections is empty?
            sections = (),
        )
        self._snapshot = self._globals.copy()
        self._updates = {}
        self._cache = {}

    def _update(self, text, flip):
        before = self._globals.copy()
        exec(text, self._globals) # XXX: Impact of modifying mutable objects?
        addupdate = []
        for name, value in self._globals.items():
            if not (name in before and value is before[name]):
                self._updates[name] = value
                addupdate.append(name)
        delete = []
        for name in before:
            if name not in self._globals:
                self._updates[name] = self.deleted
                delete.append(name)
        if addupdate:
            log.info("Add/update: %s", ', '.join(addupdate))
        if delete:
            log.info("Delete: %s", ', '.join(delete))
        if not (addupdate or delete):
            log.info('No change.')
        if flip:
            self._flip()

    def _flip(self):
        self._snapshot = self._globals.copy()
        self._updates.clear()

    def __getattr__(self, name):
        # If the _globals value (or deleted) is due to _update, return _snapshot value (or deleted):
        try:
            value = self._globals[name]
        except KeyError:
            value = self.deleted
        if name in self._updates and value is self._updates[name]:
            try:
                return self._snapshot[name]
            except KeyError:
                raise AttributeError(name)
        if value is self.deleted:
            raise AttributeError(name)
        return value

    def _cachedproperty(f):
        name = f.__name__
        code = f.__code__
        params = code.co_varnames[1:code.co_argcount]
        def fget(self):
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
        return property(fget)

    @_cachedproperty
    def sectionframecounts(self, speed, sections):
        return [speed * max(pattern.len for pattern in section) for section in sections]

    @_cachedproperty
    def totalframecount(self, sectionframecounts):
        return sum(sectionframecounts)
