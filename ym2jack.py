#!/usr/bin/env python

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
from pym2149.timer import Timer
from pym2149.ymformat import YMOpen
from pym2149.jackclient import JackClient, configure
from pym2149.config import getprocessconfig
from pym2149.vis import Roll
from pym2149.boot import createdi
from pym2149.iface import Chip
from pym2149.util import awaitinterrupt
from ymplayer import Player

log = logging.getLogger(__name__)

def main():
  config = getprocessconfig()
  config.inpath, = config.positional
  with JackClient(config) as jackclient:
    di = createdi(config)
    di.add(YMOpen)
    di.start()
    try:
      f = di(YMOpen).ym
      config.contextclock = f.clock
      configure(di)
      chip = di(Chip)
      timer = Timer(chip.clock) # TODO LATER: Support sync with jack block schedule.
      config.contextpianorollheight = f.framefreq
      di.add(Roll)
      di.add(timer)
      di.add(Player)
      di.start()
      awaitinterrupt()
    finally:
      di.stop()

if '__main__' == __name__:
  main()
