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

import sys, logging, os, anchor, lazyconf
from const import appconfigdir
from iface import Config

log = logging.getLogger(__name__)

def getconfigloader(*argnames, **kwargs):
    if 'PYM2149_CONFIG' in os.environ:
        kwargs = kwargs.copy()
        kwargs['configname'] = os.environ['PYM2149_CONFIG']
    return ConfigLoader(argnames, sys.argv[1:], **kwargs)

class ConfigLoader:

    defaultconfigname = 'defaults'
    workspacepath = os.path.join(appconfigdir, 'workspace')

    def __init__(self, argnames, args, **kwargs):
        if len(argnames) != len(args):
            raise Exception("Expected %s but got: %s" % (argnames, args))
        if 'configname' in kwargs:
            self.configname = kwargs['configname']
        else:
            confignames = [self.defaultconfigname]
            if os.path.exists(self.workspacepath):
                confignames += sorted(cn for cn in os.listdir(self.workspacepath) if os.path.exists(os.path.join(self.workspacepath, cn, 'chip.py')))
            if 1 == len(confignames): # Just defaults.
                self.configname, = confignames
            else:
                for i, cn in enumerate(confignames):
                    print >> sys.stderr, "%s) %s" % (i, cn)
                sys.stderr.write('#? ')
                self.configname = confignames[int(raw_input())]
        self.entries = zip(argnames, args)

    def load(self):
        expressions = lazyconf.Expressions()
        expressions.load(os.path.join(os.path.dirname(anchor.__file__), 'defaultconf.py'))
        if self.defaultconfigname != self.configname:
            expressions.load(os.path.join(self.workspacepath, self.configname, 'chip.py'))
        config = ConfigImpl(expressions)
        for argname, arg in self.entries:
            setattr(config, argname, arg)
        return config

class ConfigImpl(lazyconf.View, Config):

    def __init__(self, expressions):
        lazyconf.View.__init__(self, expressions)

    def fork(self):
        return Fork(self)

class Fork(lazyconf.Fork, Config): pass
