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

from __future__ import division
from pym2149.initlogging import logging
from pym2149.dosound import dosound
from pym2149.timer import Timer
from pym2149.budgie import readbytecode
from pym2149.config import getprocessconfig
from pym2149.out import newchipandstream

log = logging.getLogger(__name__)

extraseconds = 3 # TODO: Make configurable.

def main():
  config = getprocessconfig()
  inpath, label, outpath = config.positional
  f = open(inpath)
  try:
    bytecode = readbytecode(f, label)
  finally:
    f.close()
  chip, stream = newchipandstream(config, outpath)
  try:
    timer = Timer(chip.clock)
    dosound(bytecode, chip, timer, stream)
    log.info("Streaming %.3f extra seconds.", extraseconds)
    for b in timer.blocksforperiod(1 / extraseconds):
      stream.call(b)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
