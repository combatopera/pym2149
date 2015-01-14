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
from pym2149.ymformat import ymopen
from pym2149.config import getprocessconfig
from pym2149.vis import Roll
import defaultconf

log = logging.getLogger(__name__)

def main():
  defaultconf.ignoreloop = True # Even in stdout case, not sure if that's what we want.
  config = getprocessconfig()
  inpath, outpath = config.positional
  f = ymopen(inpath, config.ignoreloop)
  try:
    for info in f.info:
      log.info(info)
    chip = config.createchip(contextclockornone = f.clock)
    stream = config.createstream(chip, outpath)
    try:
      timer = Timer(chip.clock)
      roll = Roll(config.getheight(f.framefreq), chip, f.clock)
      for frame in f:
        frame(chip)
        roll.update()
        for b in timer.blocksforperiod(f.framefreq):
          stream.call(b)
      stream.flush()
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
