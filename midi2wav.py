#!/usr/bin/env pyven

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
from pym2149.out import configure
from pym2149.midi import MidiListen, MidiPump
from pym2149.config import ConfigName
from pym2149.iface import Config
from pym2149.channels import Channels
from pym2149.boot import createdi
from pym2149.util import awaitinterrupt
from pym2149.pll import PLL
from ymplayer import SimpleChipTimer

log = logging.getLogger(__name__)

def main():
    di = createdi(ConfigName('outpath'))
    di.add(PLL)
    configure(di)
    config = di(Config)
    di.add(config.mediation)
    Channels.addtodi(di)
    di.start()
    try:
        channels = di(Channels)
        log.info(channels)
        di.add(SimpleChipTimer) # One block per update.
        di.add(MidiPump)
        di.add(MidiListen)
        di.start()
        awaitinterrupt(config)
    finally:
        di.stop()

if '__main__' == __name__:
    main()
