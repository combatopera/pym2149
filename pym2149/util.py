from __future__ import division
from nod import Block
import logging

class Session:

  def __init__(self, clock):
    self.carryticks = 0
    self.clock = clock

  def block(self, refreshrate):
    available = self.carryticks + self.clock
    blockticks = int(round(available / refreshrate))
    self.carryticks = available - blockticks * refreshrate
    return Block(blockticks)

def initlogging():
  logging.basicConfig(format = "[%(levelname)s] %(message)s", level = logging.DEBUG)
