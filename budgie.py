import re

pattern = re.compile(r'^([^\s]+)?\s+([^\s]+)?\s+([^\s]+)?')

def readbytecode(f, label):
  while True:
    line = f.readline()
    if not line:
      raise Exception(label)
    groups = pattern.search(line).groups()
    if label == groups[0]:
      break
  bytecode = []
  while True:
    if groups[1] is not None:
      if 'dc.b' != groups[1].lower():
        raise Exception(groups[1])
      for s in groups[2].split(','):
        if s[0] == '%':
          n = int(s[1:], 2)
        elif s[0] == '$':
          n = int(s[1:], 16)
        # XXX: Octal?
        else:
          n = int(s)
        bytecode.append(n)
      # TODO: Support termination not just at end of line.
      if len(bytecode) >= 2 and not bytecode[-1]:
        ctrl = bytecode[-2]
        if ctrl >= 0x82 and ctrl <= 0xff:
          break
    line = f.readline()
    if not line:
      raise Exception(bytecode)
    groups = pattern.search(line).groups()
  return bytecode
