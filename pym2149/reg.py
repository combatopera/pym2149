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

class Reg(object):

  def __init__(self, value):
    self.version = 0
    self.value = value # This will increment the version to 1.

  def __setattr__(self, name, value):
    object.__setattr__(self, name, value)
    if 'value' == name:
      self.version += 1

class DerivedReg(object):

  def __init__(self, xform, *regs):
    self.versionimpl = 0,
    self.xform = xform
    self.regs = regs
    self.updateifnecessary()

  def updateifnecessary(self):
    version = self.versionimpl
    newversion = tuple(r.version for r in self.regs) + (version[-1],)
    if newversion != version:
      self.valueimpl = self.xform(*(r.value for r in self.regs))
      self.versionimpl = newversion

  def __getattr__(self, name):
    if 'value' == name:
      self.updateifnecessary()
      return self.valueimpl
    if 'version' == name:
      self.updateifnecessary()
      return self.versionimpl
    raise AttributeError(name)

  def __setattr__(self, name, value):
    if 'value' == name:
      self.valueimpl = value
      version = self.versionimpl
      self.versionimpl = version[:-1] + (version[-1] + 1,)
    else:
      object.__setattr__(self, name, value)
