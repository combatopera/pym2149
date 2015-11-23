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

from __future__ import division
from pym2149.initlogging import logging
from pym2149.jackclient import JackClient, configure
from pym2149.midi import MidiListen, MidiPump
from pym2149.config import getconfigloader
from pym2149.channels import Channels
from pym2149.boot import createdi
from pym2149.iface import Stream
from pym2149.util import awaitinterrupt
from pym2149.pll import PLL
from ymplayer import SyncTimer

log = logging.getLogger(__name__)

def main():
    config = getconfigloader().load()
    di = createdi(config)
    di.add(PLL)
    di.add(JackClient)
    di.start()
    try:
        configure(di)
        di.add(Channels)
        di.start()
        log.info(di(Channels))
        stream = di(Stream)
        log.debug("JACK block size: %s or %.3f seconds", stream.getbuffersize(), stream.getbuffersize() / config.outputrate)
        di.add(SyncTimer)
        di.add(MidiPump)
        di.add(MidiListen)
        di.start()
        awaitinterrupt(config)
    finally:
        di.stop()

if '__main__' == __name__:
    main()
