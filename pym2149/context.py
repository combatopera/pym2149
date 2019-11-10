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
from .lc import E
from .xtra import XTRA
from diapyr import types
import logging, threading, numpy as np

log = logging.getLogger(__name__)

class ContextImpl(Context):

    deleted = object()

    @types(Config)
    def __init__(self, config, sections = [(E(XTRA, '11/1'),)]):
        self._globals = self._slowglobals = dict(
            __name__ = 'pym2149.context',
            tuning = config.tuning,
            mode = 1,
            speed = 16, # XXX: Needed when sections is empty?
            sections = sections,
        )
        self._snapshot = self._globals.copy()
        self._updates = self._slowupdates = {}
        self._cache = {}
        self._slowlock = threading.Lock()
        self._fastlock = threading.Lock()

    def _update(self, text):
        addupdate = []
        delete = []
        with self._slowlock:
            with self._fastlock:
                self._globals = self._slowglobals.copy()
                self._updates = self._slowupdates.copy()
            before = self._slowglobals.copy()
            exec(text, self._slowglobals) # XXX: Impact of modifying mutable objects?
            for name, value in self._slowglobals.items():
                if not (name in before and value is before[name]):
                    self._slowupdates[name] = value
                    addupdate.append(name)
            for name in before:
                if name not in self._slowglobals:
                    self._slowupdates[name] = self.deleted
                    delete.append(name)
            with self._fastlock:
                self._globals = self._slowglobals
                self._updates = self._slowupdates
        if addupdate:
            log.info("Add/update: %s", ', '.join(addupdate))
        if delete:
            log.info("Delete: %s", ', '.join(delete))
        if not (addupdate or delete):
            log.info('No change.')

    def _flip(self):
        if self._slowlock.acquire(False):
            try:
                with self._fastlock:
                    self._snapshot = self._globals.copy()
                    self._updates.clear()
            finally:
                self._slowlock.release()

    def __getattr__(self, name):
        with self._fastlock:
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
    def _sections(self, speed, sections):
        return Sections(speed, sections)

class Sections:

    def __init__(self, speed, sections):
        self.sectionframecounts = [speed * max(pattern.len for pattern in section) for section in sections]
        self.cumulativeframecounts = np.cumsum(self.sectionframecounts)

    @property
    def totalframecount(self):
        return self.cumulativeframecounts[-1]

    def startframe(self, sectionindex):
        return self.cumulativeframecounts[sectionindex - 1] if sectionindex else 0
