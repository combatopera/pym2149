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

import sys, logging, os, aridipyimpl
from bg import SimpleBackground
from const import appconfigdir
from iface import Config

log = logging.getLogger(__name__)

class ConfigName:

    envparam = 'PYM2149_CONFIG'
    workspacepath = os.path.join(appconfigdir, 'workspace')
    configfilename = 'chip.py'
    defaultslabel = 'defaults'

    @classmethod
    def pathofname(cls, name):
        return os.path.join(cls.workspacepath, name, cls.configfilename)

    @classmethod
    def getnameornone(cls):
        try:
            name = os.environ[cls.envparam]
            return name if name else None # Empty means defaults.
        except KeyError:
            if os.path.exists(cls.workspacepath):
                confignames = sorted(name for name in os.listdir(cls.workspacepath) if os.path.exists(cls.pathofname(name)))
                for i, name in enumerate([cls.defaultslabel] + confignames):
                    print >> sys.stderr, "%s) %s" % (i, name)
                sys.stderr.write('#? ')
                number = int(raw_input())
                if number < 0:
                    raise Exception(number)
                if number:
                    return confignames[number - 1]

    def __init__(self, *params, **kwargs):
        try:
            args = kwargs['args']
        except KeyError:
            args = sys.argv[1:]
        if len(args) != len(params):
            raise Exception("Expected %s but got: %s" % (params, args))
        try:
            nameornone = kwargs['nameornone']
        except KeyError:
            nameornone = self.getnameornone()
        self.pathornone = None if nameornone is None else self.pathofname(nameornone)
        self.additems = zip(params, args)

    def isdefaults(self):
        return self.pathornone is None

    def path(self):
        if self.pathornone is None:
            raise Exception("Using %s." % self.defaultslabel)
        return self.pathornone

    def applyitems(self, config):
        for name, value in self.additems:
            setattr(config, name, value)

class PathInfo:

    defaultsmodulename = 'defaultconf'

    def __init__(self, configname):
        self.configname = configname

    def mark(self):
        path = self.configname.path()
        self.mtime = os.stat(path).st_mtime
        return path

    def load(self):
        expressions = aridipyimpl.Expressions()
        expressions.loadmodule(self.defaultsmodulename)
        if not self.configname.isdefaults():
            expressions.loadpath(self.mark())
        config = ConfigImpl(expressions)
        self.configname.applyitems(config)
        return config

    def reloadornone(self):
        path = self.configname.path()
        if os.stat(path).st_mtime != self.mtime:
            log.info("Reloading: %s", path)
            return self.load()

class ConfigSubscription(SimpleBackground):

    def __init__(self, configname, consumer):
        self.configname = configname
        self.consumer = consumer

    def start(self):
        self.pathinfo = PathInfo(self.configname)
        self.consumer(self.pathinfo.load())
        SimpleBackground.start(self, self.bg, self.Sleeper())

    def bg(self, sleeper):
        if not self.configname.isdefaults():
            while True:
                sleeper.sleep(1)
                if self.quit:
                    break
                config = self.pathinfo.reloadornone()
                if config is not None:
                    self.consumer(config)

class Private:

    def __init__(self, expressions, rootcontext):
        self.expressions = expressions
        self.contextstack = [rootcontext]

    def currentcontext(self):
        return self.contextstack[-1]

class ConfigImpl(Config):

    def __init__(self, expressions):
        self.pRiVaTe = Private(expressions, self)

    def __getattr__(self, name):
        context = self.pRiVaTe.currentcontext()
        obj = self.pRiVaTe.expressions.expression(name).resolve(context)
        for mod in self.pRiVaTe.expressions.modifiers(name):
            mod.modify(context, name, obj)
        return obj
