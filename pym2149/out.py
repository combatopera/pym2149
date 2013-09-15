import subprocess
from nod import AbstractNode

class WavWriter(AbstractNode):

  def __init__(self, clock, chip, path):
    AbstractNode.__init__(self)
    self.sox = subprocess.Popen([
      'sox',
      '-c', '1',
      '-r', str(clock),
      # Assume signal is in SoX native format:
      '-e', 'signed',
      '-b', '32',
      '-t', 'raw',
      '-',
      # TODO LATER: Output format should be configurable.
      '-r', '44100',
      '-e', 'signed',
      '-b', '16',
      path,
      # TODO: Find out whether DC filter here would be authentic.
    ], stdin = subprocess.PIPE)
    self.chip = chip

  def callimpl(self):
    self.chip(self.block).tofile(self.sox.stdin)

  def flush(self):
    if self.sox is not None:
      self.sox.stdin.close() # Send EOF.
      status = self.sox.wait()
      self.sox = None # We have released the resource(s).
      if status:
        raise Exception(status)

  def close(self):
    self.flush() # Does nothing if flush already called.
