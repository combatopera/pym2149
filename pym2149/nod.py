from buf import MasterBuf, NullBuf

class Block:

  def __init__(self, framecount):
    self.framecount = framecount

  def __repr__(self):
    return "%s(%r)" % (self.__class__.__name__, self.framecount)

class AbstractNode:

  def __init__(self):
    self.block = None

  def call(self, block):
    return self(block, False)

  def __call__(self, block, masked):
    if self.block != block:
      self.block = block
      self.masked = masked
      self.result = self.callimpl()
    return self.result

  def callimpl(self):
    raise Exception('Implement me!')

class Container(AbstractNode):

  def __init__(self, nodes):
    AbstractNode.__init__(self)
    self.nodes = nodes

  def callimpl(self):
    return [node(self.block, self.masked) for node in self.nodes]

class Node(AbstractNode):

  @staticmethod
  def commondtype(*nodes):
    dtypes = set(n.dtype for n in nodes)
    dtype, = dtypes
    return dtype

  def __init__(self, dtype, channels = 1):
    AbstractNode.__init__(self)
    masterbuf = MasterBuf(dtype)
    callimpl = self.callimpl
    def callimploverride():
      if self.masked:
        self.blockbuf = NullBuf
      else:
        self.blockbuf = masterbuf.ensureandcrop(self.block.framecount * channels)
      callimpl()
      return self.blockbuf
    self.callimpl = callimploverride
    self.dtype = dtype
