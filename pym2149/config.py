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

import sys, logging, os, anchor, lazyconf, time
from const import appconfigdir
from iface import Config
from bg import SimpleBackground
from util import singleton

log = logging.getLogger(__name__)

def getconfigloader(*argnames, **kwargs):
    if 'PYM2149_CONFIG' in os.environ:
        kwargs = kwargs.copy()
        kwargs['configname'] = os.environ['PYM2149_CONFIG']
    return ConfigLoaderImpl(argnames, sys.argv[1:], **kwargs)

class ConfigLoader: pass

@singleton
class staticconfigloader(ConfigLoader):

    def subscribe(self, consumer, config):
        consumer(config)

class ConfigLoaderImpl(ConfigLoader, SimpleBackground):

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
        self.consumers = []

    def load(self):
        expressions = lazyconf.Expressions()
        expressions.load(os.path.join(os.path.dirname(anchor.__file__), 'defaultconf.py'))
        if self.defaultconfigname != self.configname:
            self.configpath = os.path.join(self.workspacepath, self.configname, 'chip.py')
            self.mtime = os.stat(self.configpath).st_mtime
            expressions.load(self.configpath)
        config = ConfigImpl(expressions)
        for argname, arg in self.entries:
            setattr(config, argname, arg)
        return config

    def subscribe(self, consumer, config):
        consumer(config)
        self.consumers.append(consumer)

    def __call__(self):
        if not hasattr(self, 'configpath'):
            return
        while True:
            for _ in xrange(10):
                if self.quit:
                    return
                time.sleep(.1)
            if self.quit:
                return
            if os.stat(self.configpath).st_mtime == self.mtime:
                continue
            log.info("Reloading: %s", self.configpath)
            config = self.load()
            for consumer in self.consumers:
                consumer(config)

class ConfigImpl(lazyconf.View, Config):

    def __init__(self, expressions):
        lazyconf.View.__init__(self, expressions)
