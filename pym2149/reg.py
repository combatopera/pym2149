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
    self.version = 0,
    self.xform = xform
    self.regs = regs
    self.updateifnecessary()

  def updateifnecessary(self):
    version = object.__getattribute__(self, 'version')
    newversion = tuple(r.version for r in self.regs) + (version[-1],)
    if newversion != version:
      object.__setattr__(self, 'value', self.xform(*(r.value for r in self.regs)))
      self.version = newversion

  def __getattribute__(self, name):
    if 'value' == name or 'version' == name:
      self.updateifnecessary()
    return object.__getattribute__(self, name)

  def __setattr__(self, name, value):
    object.__setattr__(self, name, value)
    if 'value' == name:
      version = object.__getattribute__(self, 'version')
      self.version = version[:-1] + (version[-1] + 1,)
