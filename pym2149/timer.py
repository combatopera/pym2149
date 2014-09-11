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
from nod import Block
import logging, inspect

log = logging.getLogger(__name__)

class Timer:

  def __init__(self, clock, minblockrate = 100):
    if minblockrate is not None:
      # If division not exact, rate will slightly exceed given minimum:
      self.maxblocksize = int(clock // minblockrate)
      if not self.maxblocksize:
        raise Exception(clock, minblockrate)
    else:
      self.maxblocksize = None
    self.carryticks = 0
    self.clock = clock

  def blocks(self, refreshrate):
    available = self.carryticks + self.clock
    blockticks = int(round(available / refreshrate))
    self.carryticks = available - blockticks * refreshrate
    if self.maxblocksize is not None:
      while blockticks:
        size = min(blockticks, self.maxblocksize)
        b = Block(size)
        blockticks -= size
        yield b
    else:
      yield Block(blockticks)

  def __del__(self): # XXX: Reliable enough?
    if self.carryticks:
      context = inspect.stack()[1]
      log.warn("Non-zero end of session carry %s in %s before line %s.", self.carryticks, context[1], context[2])
