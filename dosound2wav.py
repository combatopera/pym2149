#!/usr/bin/env pyven

# Copyright 2014, 2018 Andrzej Cichocki

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
from pym2149.dosound import dosound
from pym2149.timer import Timer
from pym2149.budgie import readbytecode
from pym2149.config import ConfigName
from pym2149.out import configure
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream, Config
from pym2149.timerimpl import ChipTimer
from diapyr.start import Started

log = logging.getLogger(__name__)

def main():
    di = createdi(ConfigName('inpath', 'srclabel', 'outpath'))
    config = di(Config)
    f = open(config.inpath)
    try:
        bytecode = readbytecode(f, config.srclabel)
    finally:
        f.close()
    configure(di)
    chip = di(Chip)
    try:
        di.all(Started)
        di.add(ChipTimer)
        timer = di(Timer)
        stream = di(Stream)
        dosound(bytecode, chip, timer, stream)
        log.info("Streaming %.3f extra seconds.", config.dosoundextraseconds)
        for b in timer.blocksforperiod(1 / config.dosoundextraseconds):
            stream.call(b)
        stream.flush()
    finally:
        di.discardall()

if '__main__' == __name__:
    main()
