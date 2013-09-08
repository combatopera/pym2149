class Register(object):

  def __init__(self, value):
    self.version = 0
    self.value = value

  def __setattr__(self, name, value):
    object.__setattr__(self, name, value)
    if 'value' == name:
      self.version += 1
