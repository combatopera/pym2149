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

import logging, inspect

log = logging.getLogger(__name__)

def types(*deptypes, **kwargs):
    def g(f):
        f.di_deptypes = deptypes
        if 'this' in kwargs:
            f.di_owntype = kwargs['this']
        return f
    return g

class Source:

    class Static: startable, stoppable = False, False

    class Stopped: startable, stoppable = True, False

    class Started: startable, stoppable = False, True

    def __init__(self, type, di):
        self.types = set()
        def addtype(type):
            self.types.add(type)
            for base in type.__bases__:
                if base not in self.types:
                    addtype(base)
        addtype(type)
        self.typelabel = "%s.%s" % (type.__module__, type.__name__)
        # We assume stop exists if start does:
        self.lifecycle = self.Stopped if hasattr(type, 'start') else self.Static
        self.di = di

    def tostarted(self):
        if self.lifecycle.startable:
            instance = self() # Observe we only instantiate if startable.
            log.debug("Starting: %s", self.typelabel)
            instance.start() # On failure we assume state unchanged from Stopped.
            self.lifecycle = self.Started
            return True # Notify caller a transition to Started actually happened.

    def tostopped(self):
        if self.lifecycle.stoppable:
            instance = self() # Should already exist.
            log.debug("Stopping: %s", self.typelabel)
            try:
                instance.stop()
            except:
                self.di.error("Failed to stop an instance of %s:", self.typelabel, exc_info = True)
            self.lifecycle = self.Stopped # Even on failure, we don't attempt to stop again.

class Instance(Source):

    def __init__(self, instance, di):
        Source.__init__(self, instance.__class__, di)
        self.instance = instance

    def __call__(self):
        return self.instance

class Creator(Source):

    def __init__(self, callable, di):
        Source.__init__(self, self.getowntype(callable), di)
        self.instance = None
        self.callable = callable

    def __call__(self):
        if self.instance is None:
            log.debug("%s: %s", self.action, self.typelabel)
            deptypes, defaults = self.getdeptypesanddefaults(self.callable)
            if defaults:
                args = [self.di(t) for t in deptypes[:-len(defaults)]]
                args += [self.di(t, default = d) for t, d in zip(deptypes[-len(defaults):], defaults)]
            else:
                args = [self.di(t) for t in deptypes]
            self.instance = self.callable(*args)
        return self.instance

class Class(Creator):

    action = 'Instantiating'

    @staticmethod
    def getowntype(clazz):
        return clazz

    def getdeptypesanddefaults(self, clazz):
        ctor = getattr(clazz, '__init__')
        defaults = inspect.getargspec(ctor).defaults
        try:
            return ctor.di_deptypes, defaults
        except AttributeError:
            raise Exception("Missing types annotation: %s" % self.typelabel)

class Factory(Creator):

    action = 'Fabricating'

    @staticmethod
    def getowntype(factory):
        return factory.di_owntype

    @staticmethod
    def getdeptypesanddefaults(factory):
        return factory.di_deptypes, inspect.getargspec(factory).defaults

class DI:

    error = log.error # Tests may override.

    def __init__(self):
        self.typetosources = {}
        self.allsources = [] # Old-style classes won't be registered against object.

    def addsource(self, source):
        for type in source.types:
            try:
                self.typetosources[type].append(source)
            except KeyError:
                self.typetosources[type] = [source]
        self.allsources.append(source)

    def addclass(self, clazz):
        self.addsource(Class(clazz, self))

    def addinstance(self, instance):
        self.addsource(Instance(instance, self))

    def addfactory(self, factory):
        self.addsource(Factory(factory, self))

    def add(self, obj):
        if hasattr(obj, 'di_owntype'):
            addmethods = self.addfactory,
        elif hasattr(obj, '__class__'):
            clazz = obj.__class__
            if clazz == type: # It's a non-fancy class.
                addmethods = self.addclass,
            elif isinstance(obj, type): # It's a fancy class.
                addmethods = self.addclass, self.addinstance
            else: # It's an instance.
                addmethods = self.addinstance,
        else: # It's an old-style class.
            addmethods = self.addclass,
        for m in addmethods:
            m(obj)
        return addmethods

    def all(self, type):
        return [source() for source in self.typetosources.get(type, [])]

    def __call__(self, type, **kwargs):
        objs = self.all(type)
        if not objs and 'default' in kwargs:
            return kwargs['default']
        if 1 != len(objs):
            raise Exception("Expected 1 object of type %s but got: %s" % (type, len(objs)))
        return objs[0]

    def start(self):
        started = []
        for source in self.allsources:
            try:
                source.tostarted() and started.append(source)
            except:
                for t in reversed(started): # Don't unroll previous batches.
                    t.tostopped()
                raise

    def stop(self):
        for source in reversed(self.allsources):
            source.tostopped()
