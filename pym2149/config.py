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
from aridity.config import ConfigCtrl
from aridity.model import wrap
from diapyr import DI, types, UnsatisfiableRequestException
from importlib import import_module
from pathlib import Path
import logging, sys

log = logging.getLogger(__name__)

class ConfigName:

    namespace = 'pym2149'

    def __init__(self, *params, args = sys.argv[1:], name = 'root'):
        parser = ArgumentParser()
        parser.add_argument('--config', action = 'append', default = [])
        parser.add_argument('--ignore-settings', action = 'store_true')
        for param in params:
            parser.add_argument(param)
        self.additems = parser.parse_args(args)
        self.path = Path(__file__).resolve().parent / f"{name}.arid"

    @types(DI, this = Config)
    def loadconfig(self, di):
        config = ConfigCtrl()
        config.put('enter', function = enter)
        config.put('py', function = lambda *args: py(getattr(config.node, self.namespace), *args))
        config.put('resolve', function = lambda *args: AsScope.resolve(di, *args))
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
                            repl(f"\t{line}")
            else:
                setattr(getattr(config.node, self.namespace), name, value)
        return getattr(config.node, self.namespace)

class AsScope:

    @classmethod
    def resolve(cls, di, scope, resolvable):
        try:
            return cls(scope, di(_getglobal(scope, resolvable).scalar))
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

def _getglobal(scope, resolvable):
    spec = resolvable.resolve(scope).cat()
    lastdot = spec.rindex('.')
    return wrap(getattr(import_module(spec[:lastdot], __package__), spec[lastdot + 1:]))

def enter(scope, scoperesolvable, resolvable):
    return resolvable.resolve(scoperesolvable.resolve(scope))

def py(config, scope, *clauses):
    return wrap(eval(' '.join(c.cat() for c in clauses), dict(config = config)))
