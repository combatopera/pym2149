# Copyright 2014, 2018, 2019 Andrzej Cichocki

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
from splut.bg import SimpleBackground
from aridity import Context, Repl
from aridimpl.util import NoSuchPathException
from aridimpl.model import Function, Number, Text
from diapyr import UnsatisfiableRequestException
from pathlib import Path
import sys, logging, numbers, importlib, argparse

log = logging.getLogger(__name__)

class ConfigName:

    def __init__(self, *params, args = sys.argv[1:], name = 'defaultconf'):
        parser = argparse.ArgumentParser()
        parser.add_argument('--repr', action = 'append', default = [])
        parser.add_argument('--log', default = '-')
        for param in params:
            parser.add_argument(param)
        self.additems = parser.parse_args(args)
        self.path = Path(__file__).resolve().parent / ("%s.arid" % name)

    def applyitems(self, context):
        for name, value in self.additems.__dict__.items():
            context[name,] = wrap(value)

    def newloader(self, di):
        return ConfigLoader(self, di)

def wrap(value):
    return (Number if isinstance(value, numbers.Number) else Text)(value)

class AsContext:

    def __init__(self, parent, obj):
        self.parent = parent
        self.obj = obj

    def resolved(self, name):
        try:
            return wrap(getattr(self.obj, name))
        except AttributeError:
            return self.parent.resolved(name)

class ConfigLoader:

    @staticmethod
    def getglobal(context, resolvable):
        spec = resolvable.resolve(context).cat()
        lastdot = spec.rindex('.')
        return wrap(getattr(importlib.import_module(spec[:lastdot], __package__), spec[lastdot + 1:]))

    @staticmethod
    def enter(context, contextresolvable, resolvable):
        return resolvable.resolve(contextresolvable.resolve(context))

    @staticmethod
    def py(config, context, *clauses):
        return wrap(eval(' '.join(c.cat() for c in clauses), dict(config = config)))

    def resolve(self, context, resolvable):
        try:
            return AsContext(context, self.di(self.getglobal(context, resolvable).value))
        except UnsatisfiableRequestException:
            raise NoSuchPathException

    def __init__(self, configname, di):
        self.configname = configname
        self.di = di

    def mark(self):
        path = self.configname.path
        self.mtime = path.stat().st_mtime
        return path

    def load(self):
        context = Context()
        context['global',] = Function(self.getglobal)
        context['enter',] = Function(self.enter)
        context['py',] = Function(lambda *args: self.py(config, *args))
        context['resolve',] = Function(self.resolve)
        self.configname.applyitems(context)
        with Repl(context) as repl:
            path = self.mark()
            repl.printf("cwd = %s", path.parent)
            repl.printf(". %s", path.name)
            settings = Path.home() / '.settings.arid'
            if settings.exists():
                repl.printf(". %s", settings)
        config = ConfigImpl(context)
        return config

    def reloadornone(self):
        path = self.configname.path
        if path.stat().st_mtime != self.mtime:
            log.info("Reloading: %s", path)
            return self.load()

class ConfigSubscription(SimpleBackground):

    def __init__(self, profile, configname, di, consumer):
        super().__init__(profile)
        self.configname = configname
        self.di = di
        self.consumer = consumer

    def start(self):
        self.loader = self.configname.newloader(self.di)
        self.consumer(self.loader.load())
        super().start(self.bg, self.Sleeper())

    def bg(self, sleeper):
        while True:
            sleeper.sleep(1)
            if self.quit:
                break
            config = self.loader.reloadornone()
            if config is not None:
                self.consumer(config)

class ConfigImpl(Config):

    def __init__(self, context):
        self.pRiVaTe = context

    def __getattr__(self, name):
        try:
            return self[(name,)].unravel()
        except NoSuchPathException:
            raise AttributeError(name)

    def __getitem__(self, path):
        return self.pRiVaTe.resolved(*path)
