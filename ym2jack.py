#!/usr/bin/env runpy

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

from pym2149.initlogging import logging
from pym2149.ymformat import YMOpen
from pym2149.jackclient import JackClient, configure
from pym2149.config import getconfigloader
from pym2149.vis import Roll
from pym2149.boot import createdi
from pym2149.util import awaitinterrupt
from ymplayer import Player, SyncTimer

log = logging.getLogger(__name__)

def main():
    config = getconfigloader('inpath').load()
    di = createdi(config)
    di.add(JackClient)
    di.add(YMOpen)
    di.start()
    try:
        configure(di)
        di.add(Roll)
        di.add(SyncTimer)
        di.add(Player)
        di.start()
        awaitinterrupt(config)
    finally:
        di.stop()

if '__main__' == __name__:
    main()
