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

from ..iface import Config, Context
from ..foxdotlib import FoxDotListen
from diapyr import types
import logging

log = logging.getLogger(__name__)

class Handler:

    addresses = '/lc',

    @types(Context)
    def __init__(self, context):
        self.context = context

    def __call__(self, timetags, message, reply):
        try:
            text, = message.args
            diff = self.context._update(text)
            log.info("Add/update: %s", ', '.join(diff.keys()))
        except Exception:
            log.exception('Update failed:')

class Listen(FoxDotListen):

    configkey = 'pym2149'

    @types(Config, [Handler])
    def __init__(self, config, handlers):
        super().__init__(config, handlers)

def configure(di):
    di.add(Handler)
    di.add(Listen)
