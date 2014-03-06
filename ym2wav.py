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
from pym2149.util import Timer
from pym2149.ymformat import ymopen
from pym2149.mix import IdealMixer
from pym2149.pitch import Period
from cli import Config
import sys

log = logging.getLogger(__name__)

class Roll:

  shapes = ('\\_',) * 4 + ('/_',) * 4 + ('\\\\', '\\_', '\\/', '\\-', '//', '/-', '/\\', '/_')

  def __init__(self, height, chip, nomclock):
    self.line = 0
    self.jump = "\x1b[%sA" % height
    self.format = ' | '.join(chip.channels * ["%7s %1s %2s %1s %2s %7s"])
    self.height = height
    self.chip = chip
    self.nomclock = nomclock

  def update(self):
    if self.line == self.height:
      sys.stderr.write(self.jump)
      self.line = 0
    vals = []
    for c in xrange(self.chip.channels):
      tone = self.chip.toneflags[c].value
      noise = self.chip.noiseflags[c].value
      env = self.chip.levelmodes[c].value
      level = self.chip.fixedlevels[c].value
      rhs = env or level
      if tone and rhs:
        vals.append(Period(self.chip.toneperiods[c].value).tonefreq(self.nomclock).pitch())
      else:
        vals.append('')
      if tone and noise and rhs:
        vals.append('&')
      else:
        vals.append('')
      if noise and rhs:
        vals.append(self.chip.noiseperiod.value)
      else:
        vals.append('')
      if (tone or noise) and rhs:
        vals.append('*')
      else:
        vals.append('')
      if env:
        shape = self.chip.envshape.value
        vals.append(self.shapes[shape])
        vals.append(Period(self.chip.envperiod.value).envfreq(self.nomclock, shape).pitch())
      elif level:
        vals.append(level)
        vals.append('')
      else:
        vals.append('')
        vals.append('')
    print >> sys.stderr, self.format % tuple(vals)
    self.line += 1

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
      timer = Timer(chip.clock)
      roll = Roll(config.getheight(f.framefreq), chip, f.clock)
      for frame in f:
        frame(chip)
        roll.update()
        for b in timer.blocks(f.framefreq):
          stream.call(b)
      stream.flush()
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
