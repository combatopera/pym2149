from __future__ import division
from nod import Block
import logging, inspect

log = logging.getLogger(__name__)

class Session:

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
