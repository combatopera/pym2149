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
from pym2149 import out
from pym2149.boot import boot
from pym2149.channels import Channels
from pym2149.config import ConfigName
from pym2149.midi import MidiListen, EventPump
from pym2149.pll import PLL
from pym2149.timerimpl import SimpleChipTimer
from pym2149.util import MainThread
from diapyr.start import Started

log = logging.getLogger(__name__)

def main_midi2wav():
    config, di = boot(ConfigName('outpath', name = 'realtime'))
    try:
        di.add(PLL)
        out.configure(di)
        di.add(config.mediation)
        Channels.configure(di)
        di.all(Started)
        channels = di(Channels)
        log.info(channels)
        di.add(SimpleChipTimer)
        di.add(EventPump)
        di.add(MidiListen)
        di.all(Started)
        di(MainThread).sleep()
    finally:
        di.discardall()
