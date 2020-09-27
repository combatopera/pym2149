# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .iface import Config
from argparse import ArgumentParser
from aridity import NoSuchPathException
from aridity.model import Number, Text
from diapyr import UnsatisfiableRequestException
from importlib import import_module
from pathlib import Path
import aridity.config, logging, lurlene, numbers, sys

log = logging.getLogger(__name__)

class ConfigImpl(aridity.config.Config, Config, lurlene.iface.Config): pass

class ConfigName:

    namespace = 'pym2149'

    def __init__(self, *params, args = sys.argv[1:], name = 'defaultconf'):
        parser = ArgumentParser()
        parser.add_argument('--repr', action = 'append', default = [])
        parser.add_argument('--config', action = 'append', default = [])
        parser.add_argument('--ignore-settings', action = 'store_true')
        for param in params:
            parser.add_argument(param)
        self.additems = parser.parse_args(args)
        self.path = Path(__file__).resolve().parent / ("%s.arid" % name)

    def loadconfig(self, di):
        config = ConfigImpl.blank()
        config.put('global', function = getglobal)
        config.put('enter', function = enter)
        config.put('py', function = lambda *args: py(getattr(config, self.namespace), *args))
        config.put('resolve', function = lambda *args: AsContext.resolve(di, *args))
        config.printf("cwd = %s", self.path.parent)
        config.printf("%s . %s", self.namespace, self.path.name)
        if not self.additems.ignore_settings:
            try:
                config.loadsettings()
            except FileNotFoundError as e:
                log.warning("Settings not found: %s", e)
        for name, value in self.additems.__dict__.items():
            if 'config' == name:
                with config.repl() as repl:
                    for text in value:
                        repl.printf("%s", self.namespace)
                        for line in text.splitlines():
                            repl("\t%s" % line)
            else:
                config.put(self.namespace, name, resolvable = wrap(value))
        return getattr(config, self.namespace)

def wrap(value): # TODO: Migrate to aridity.
    return (Number if isinstance(value, numbers.Number) else Text)(value)

class AsContext:

    @classmethod
    def resolve(cls, di, context, resolvable):
        try:
            return cls(context, di(getglobal(context, resolvable).value))
        except UnsatisfiableRequestException:
            raise NoSuchPathException

    def __init__(self, parent, obj):
        self.parent = parent
        self.obj = obj

    def resolved(self, name):
        try:
            return wrap(getattr(self.obj, name))
        except AttributeError:
            return self.parent.resolved(name)

def getglobal(context, resolvable):
    spec = resolvable.resolve(context).cat()
    lastdot = spec.rindex('.')
    return wrap(getattr(import_module(spec[:lastdot], __package__), spec[lastdot + 1:]))

def enter(context, contextresolvable, resolvable):
    return resolvable.resolve(contextresolvable.resolve(context))

def py(config, context, *clauses):
    return wrap(eval(' '.join(c.cat() for c in clauses), dict(config = config)))
