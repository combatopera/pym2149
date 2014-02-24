from __future__ import division
import sys, logging, getopt
from pym2149.ym2149 import YM2149, defaultscale

log = logging.getLogger(__name__)

class Config:

  @staticmethod
  def uniqueoption(options, keys, defaultval, xform):
    vals = [v for k, v in options if k in keys]
    if not vals:
      return defaultval
    v, = vals
    return xform(v)

  @staticmethod
  def booleanoption(options, keys):
    for k, _ in options:
      if k in keys:
        return True
    return False

  def __init__(self):
    options, self.args = getopt.getopt(sys.argv[1:], 's:p1', ['scale=', 'pause', 'once'])
    self.scale = self.uniqueoption(options, ('-s', '--scale'), defaultscale, int)
    self.pause = self.booleanoption(options, ('-p', '--pause'))
    self.once = self.booleanoption(options, ('-1', '--once'))

  def createchip(self, nominalclock, **kwargs):
    chip = YM2149(scale = self.scale, pause = self.pause, **kwargs)
    chip.clock = int(round(nominalclock * self.scale / 8))
    if self.scale != defaultscale:
      log.debug("Clock adjusted to %.3f for non-standard scale.", chip.clock)
    return chip
