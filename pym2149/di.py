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

def types(*types):
    def g(f):
        f.di_types = types
        return f
    return g

class Adapter:

    def __init__(self, type):
        self.types = set()
        def addtype(type):
            self.types.add(type)
            for base in type.__bases__:
                if base not in self.types:
                    addtype(base)
        addtype(type)

class Instance(Adapter):

    def __init__(self, instance):
        Adapter.__init__(self, instance.__class__)
        self.instance = instance

    def __call__(self):
        return self.instance

class Class(Adapter):

    def __init__(self, clazz, di):
        Adapter.__init__(self, clazz)
        self.instance = None
        self.clazz = clazz
        self.di = di

    def __call__(self):
        if self.instance is None:
            log.debug("Instantiating: %s", self.clazz)
            objs = []
            ctor = getattr(self.clazz, '__init__')
            try:
                types = ctor.di_types
            except AttributeError:
                raise Exception("Missing types annotation: %s" % self.clazz)
            for t in types:
                obj, = self.di.getorcreate(t)
                objs.append(obj)
            self.instance = self.clazz(*objs)
        return self.instance

class DI:

    def __init__(self):
        self.typetoadapters = {}

    def addadapter(self, adapter):
        for type in adapter.types:
            try:
                self.typetoadapters[type].append(adapter)
            except KeyError:
                self.typetoadapters[type] = [adapter]

    def addclass(self, clazz):
        self.addadapter(Class(clazz, self))

    def addinstance(self, instance):
        self.addadapter(Instance(instance))

    def add(self, obj):
        if hasattr(obj, '__class__'):
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

    def getorcreate(self, type):
        return [adapter() for adapter in self.typetoadapters.get(type, [])]
