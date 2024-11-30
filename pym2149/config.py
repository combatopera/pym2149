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
from aridity.model import Boolean, wrap
from diapyr import DI, types, UnsatisfiableRequestException
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
        cc = ConfigCtrl()
        cc.w.istry = istry
        cc.w.pyattr = pyattr
        cc.w.py = py
        cc.w.diref = DIRef(di)
        cc.printf("cwd = %s", self.path.parent)
        cc.printf("%s . %s", self.namespace, self.path.name)
        if not self.additems.ignore_settings:
            try:
                cc.loadsettings()
            except FileNotFoundError as e:
                log.warning("Settings not found: %s", e)
        for name, value in self.additems.__dict__.items():
            if 'config' == name:
                with cc.repl() as repl:
                    for text in value:
                        repl.printf("%s", self.namespace)
                        for line in text.splitlines():
                            repl(f"\t{line}")
            else:
                setattr(getattr(cc.node, self.namespace), name, value)
        return getattr(cc.node, self.namespace)

class DIRef:

    def __init__(self, di):
        self.di = di

    def __call__(self, scope, resolvable):
        try:
            return wrap(self.di(resolvable.resolve(scope).scalar))
        except UnsatisfiableRequestException:
            raise NoSuchPathException

def istry(scope, resolvable):
    try:
        resolvable.resolve(scope)
        val = True
    except NoSuchPathException:
        val = False
    return Boolean(val)

def pyattr(scope, objresolvable, attrresolvable):
    return wrap(getattr(objresolvable.resolve(scope).scalar, attrresolvable.resolve(scope).cat()))

def py(scope, coderesolvable):
    return wrap(eval(coderesolvable.resolve(scope).cat(), {}))
