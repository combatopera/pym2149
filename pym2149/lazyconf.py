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

import re, logging, sys, os

log = logging.getLogger(__name__)

class Expression:

    def __init__(self, head, code, name):
        self.head = head
        self.code = code
        self.name = name

    def __call__(self, view, itemornone = None):
        g = dict(config = view)
        if itemornone is not None:
            g[itemornone[0]] = itemornone[1]
        exec (self.head, g)
        exec (self.code, g)
        if itemornone is None:
            return g[self.name]

class View:

    def __init__(self, loader):
        self.loader = loader

    def __getattr__(self, name):
        if 'configpath' == name:
            return self.loader.paths[-1]
        obj = self.loader.expressions[name](self)
        for mod in self.loader.modifiers(name):
            mod(self, (name, obj))
        return obj

    def addpath(self, path):
        if path not in sys.path:
            sys.path.append(path)

class Loader:

    # TODO LATER: Ideally inspect the AST as this can give false positives.
    toplevelassignment = re.compile(r'^([^\s]+)\s*=')

    @staticmethod
    def canonicalize(path):
        while True:
            try:
                link = os.readlink(path)
            except OSError:
                return path
            path = os.path.join(os.path.dirname(path), link)

    def __init__(self):
        self.expressions = {}
        self.paths = []

    def load(self, path):
        f = open(path)
        try:
            head = []
            line = f.readline()
            while line and self.toplevelassignment.search(line) is None:
                head.append(line)
                line = f.readline()
            tocode = lambda block: compile(block, '<string>', 'exec')
            log.debug("[%s] Header is first %s lines.", path, len(head))
            head = tocode(''.join(head))
            while line:
                m = self.toplevelassignment.search(line)
                if m is not None:
                    name = m.group(1)
                    self.expressions[name] = Expression(head, tocode(line), name)
                line = f.readline()
        finally:
            f.close()
        self.paths.append(self.canonicalize(path))

    def modifiers(self, name):
        for modname, e in self.expressions.iteritems():
            if modname.startswith(name + '['):
                yield e
