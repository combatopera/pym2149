#!/usr/bin/env pyven

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

from pym2149.initlogging import logging
from pym2149 import jackclient
from pym2149.boot import boot
from pym2149.config import ConfigName
from pym2149.iface import Config, Context
from pym2149.lc import osc as lc_osc
from pym2149.lc.bridge import LiveCodingBridge
from pym2149.timerimpl import SyncTimer
from pym2149.util import MainThread
from pym2149.ymplayer import Player
from diapyr import types
from diapyr.start import Started

log = logging.getLogger(__name__)

@types(Config, Context, this = Started)
def loadcontext(config, context):
    with open(config.inpath) as f:
        context._update(f.read(), True)

def main():
    config, di = boot(ConfigName('inpath', '--section'))
    try:
        di.add(loadcontext)
        di.add(LiveCodingBridge)
        lc_osc.configure(di)
        jackclient.configure(di)
        di.add(SyncTimer)
        di.add(Player)
        di.all(Started)
        di(MainThread).sleep()
    finally:
        di.discardall()

if '__main__' == __name__:
    main()
