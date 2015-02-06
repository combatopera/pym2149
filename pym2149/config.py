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
import sys, logging, os, anchor
from lazyconf import Loader, View
from const import appconfigdir

log = logging.getLogger(__name__)

def getprocessconfig(*argnames):
  return Config(argnames, sys.argv[1:])

class Config(View):

  def __init__(self, argnames, args):
    if len(argnames) != len(args):
      raise Exception("Expected %s but got: %s" % (argnames, args))
    loader = Loader()
    View.__init__(self, loader)
    for argname, arg in zip(argnames, args):
      setattr(self, argname, arg)
    loader.load(os.path.join(os.path.dirname(anchor.__file__), 'defaultconf.py'))
    configspath = os.path.join(appconfigdir, 'configs')
    defaultconfigname = 'defaults'
    confignames = [defaultconfigname]
    if os.path.exists(configspath):
      confignames += sorted(os.listdir(configspath))
    if 1 == len(confignames):
      configname, = confignames
    else:
      for i, cn in enumerate(confignames):
        print >> sys.stderr, "%s) %s" % (i, cn)
      sys.stderr.write('#? ')
      configname = confignames[int(raw_input())]
    if defaultconfigname != configname:
      loader.load(os.path.join(configspath, configname))
