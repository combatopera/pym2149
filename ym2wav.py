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
from pym2149.out import WavWriter
from pym2149.util import Session
from pym2149.ymformat import ymopen
from pym2149.mix import IdealMixer
from cli import Config

log = logging.getLogger(__name__)

def main():
  config = Config()
  inpath, outpath = config.args
  f = ymopen(inpath, config)
  try:
    for info in f.info:
      log.info(info)
    chip = config.createchip(f.clock)
    stream = WavWriter(chip.clock, IdealMixer(chip), outpath)
    try:
      session = Session(chip.clock)
      for frame in f:
        chip.update(frame)
        for b in session.blocks(f.framefreq):
          stream.call(b)
      stream.flush()
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
