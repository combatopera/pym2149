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
from pym2149.jackclient import JackClient
from pym2149.nod import Block
from pym2149.midi import Midi
from pym2149.config import getprocessconfig
from pym2149.channels import Channels

log = logging.getLogger(__name__)

def main():
  config = getprocessconfig()
  midi = Midi(config)
  with JackClient(config) as jackclient:
      chip, stream = jackclient.newchipandstream()
      try:
        channels = Channels(config, chip)
        log.info(channels)
        blocksizeseconds = stream.size / config.outputrate
        log.debug("JACK block size: %s or %.3f seconds", stream.size, blocksizeseconds)
        log.info("Chip update rate for arps and slides: %.3f Hz", 1 / blocksizeseconds)
        minbleps = stream.wavs[0].minbleps
        naivex = 0
        frame = 0
        while True:
          # TODO: For best mediation, advance note-off events that would cause instantaneous polyphony.
          for event in midi.iterevents():
            log.debug("%s @ %s -> %s", event, frame, event(channels, frame))
          channels.updateall(frame)
          # Make min amount of chip data to get one JACK block:
          naiven = minbleps.getminnaiven(naivex, stream.size)
          stream.call(Block(naiven))
          channels.applyrates()
          naivex = (naivex + naiven) % chip.clock
          frame += 1
      finally:
        stream.close()

if '__main__' == __name__:
  main()
