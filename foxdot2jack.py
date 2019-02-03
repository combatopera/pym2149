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
from pym2149 import jackclient, foxdot
from pym2149.midi import EventPump
from pym2149.config import ConfigName
from pym2149.channels import Channels
from pym2149.boot import boot
from pym2149.util import awaitinterrupt
from pym2149.pll import PLL
from pym2149.timerimpl import SyncTimer
from diapyr.start import Started

log = logging.getLogger(__name__)

def main():
    config, di = boot(ConfigName(name = 'foxdot'))
    try:
        di.add(PLL) # XXX: Can we crank up the updaterate instead? It's 44100/64=689 in SC.
        di.add(jackclient.JackClient)
        di.add(config.mediation)
        Channels.configure(di)
        di.add(SyncTimer)
        foxdot.configure(di)
        jackclient.configure(di)
        di.add(EventPump)
        di.all(Started)
        log.info(di(Channels))
        awaitinterrupt(config)
    finally:
        di.discardall()

if '__main__' == __name__:
    main()
