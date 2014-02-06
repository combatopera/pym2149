import subprocess
from nod import AbstractNode

class WavWriter(AbstractNode):

  def __init__(self, clock, chip, path):
    AbstractNode.__init__(self)
    outfreq = 44100
    command = [
      'sox',
      '-r', str(clock),
      '-e', 'float',
      '-b', '32',
      '-t', 'raw',
      '-',
      '-r', str(outfreq),
      '-e', 'signed',
      '-b', '16',
    ]
    if '-' == path:
      command += ['-t', 'wav']
    elif '/dev/null' == path:
      command += ['-t', 'raw']
    command += [path]
    # TODO: Find out whether a DC filter would be authentic.
    self.sox = subprocess.Popen(command, stdin = subprocess.PIPE)
    self.chip = chip

  def callimpl(self):
    self.chain(self.chip).tofile(self.sox.stdin)

  def flush(self):
    if self.sox is not None:
      self.sox.stdin.close() # Send EOF.
      status = self.sox.wait()
      self.sox = None # We have released the resource(s).
      if status:
        raise Exception(status)

  def close(self):
    self.flush() # Does nothing if flush already called.
