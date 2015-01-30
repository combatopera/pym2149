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
from pym2149.dosound import dosound
from pym2149.timer import Timer
from pym2149.config import getprocessconfig
from pym2149.out import configure, Stream
from pym2149.di import DI
from pym2149.ym2149 import Chip

log = logging.getLogger(__name__)

def main():
  config = getprocessconfig()
  config.inpath, config.outpath = config.positional
  f = open(config.inpath, 'rb')
  try:
    log.debug("Total ticks: %s", (ord(f.read(1)) << 8) | ord(f.read(1)))
    bytecode = [ord(c) for c in f.read()]
  finally:
    f.close()
  di = DI()
  di.add(config)
  configure(di)
  chip = di(Chip)
  stream = di(Stream)
  try:
    dosound(bytecode, chip, Timer(chip.clock), stream)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
