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

    @types(Config)
    def __init__(self, config):
        self._dict = dict(
            __name__ = 'pym2149.context',
            tuning = config.tuning,
            mode = 1,
            speed = 16,
            sections = [[unit]],
        )

    def _update(self, text):
        snapshot = self._dict.copy()
        exec(text, self._dict)
        return {name: obj for name, obj in self._dict.items()
                if name not in snapshot or obj is not snapshot[name]}

    def __getattr__(self, name):
        try:
            return self._dict[name]
        except KeyError:
            raise AttributeError(name)

    @property
    def sectionframecounts(self):
        # FIXME: Cache this.
        return [self.speed * max(pattern.len for pattern in section if pattern is not None) for section in self.sections]
