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

import logging

log = logging.getLogger(__name__)

def types(*deptypes, **kwargs):
    def g(f):
        f.di_deptypes = deptypes
        if 'this' in kwargs:
            f.di_owntype = kwargs['this']
        return f
    return g

class Source:

    def __init__(self, type):
        self.types = set()
        def addtype(type):
            self.types.add(type)
            for base in type.__bases__:
                if base not in self.types:
                    addtype(base)
        addtype(type)
        self.typelabel = "%s.%s" % (type.__module__, type.__name__)
        self.di = di

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
            self.instance = self.callable(*(self.di(t) for t in self.getdeptypes(self.callable)))
        return self.instance

class Class(Creator):

    action = 'Instantiating'

    @staticmethod
    def getowntype(clazz):
        return clazz

    def getdeptypes(self, clazz):
        ctor = getattr(clazz, '__init__')
        try:
            return ctor.di_deptypes
        except AttributeError:
            raise Exception("Missing types annotation: %s" % self.typelabel)

class Factory(Creator):

    action = 'Fabricating'

    @staticmethod
    def getowntype(factory):
        return factory.di_owntype

    @staticmethod
    def getdeptypes(factory):
        return factory.di_deptypes

class DI:

    def __init__(self):
        self.typetosources = {}

    def addsource(self, source):
        for type in source.types:
            try:
                self.typetosources[type].append(source)
            except KeyError:
                self.typetosources[type] = [source]

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

    def __call__(self, type):
        obj, = self.all(type)
        return obj
