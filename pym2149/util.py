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

from .iface import Config
from diapyr import types
from contextlib import contextmanager
import time, logging

log = logging.getLogger(__name__)

def singleton(t):
    return t()

class MainThread:

    @types(Config)
    def __init__(self, config):
        self.profile = config.profile
        self.trace = config.trace

    def sleep(self):
        if self.profile or self.trace:
            sleeptime = self.profile.time if self.profile else self.trace
            log.debug("Continue for %.3f seconds.", sleeptime)
            time.sleep(sleeptime)
            log.debug('End of profile, shutting down.')
        else:
            log.debug('Continue until interrupt.')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                log.debug('Caught interrupt, shutting down.')

class EMA:

    def __init__(self, alpha, initial):
        self.alpha = alpha
        self.value = initial

    def __call__(self, instantaneous):
        self.value = self.alpha * instantaneous + (1 - self.alpha) * self.value
        return self.value

def ceildiv(numerator, denominator):
    return (numerator + denominator - 1) // denominator

def outerzip(*iterables):
    iterators = [iter(i) for i in iterables]
    def g():
        nonlocal running
        for i in iterators:
            try:
                yield next(i)
            except StopIteration:
                running -= 1
                yield
    n = len(iterators)
    while True:
        running = n
        values = tuple(g())
        if not running:
            break
        yield values

class ExceptionCatcher:

    _onfire = False

    @contextmanager
    def catch(self, *args):
        try:
            yield
            self._onfire = False
        except Exception:
            if not self._onfire: # TODO: Show error if it has changed.
                log.exception(*args)
                self._onfire = True
