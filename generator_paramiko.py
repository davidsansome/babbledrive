import generator

import os.path

class ParamikioGenerator(generator.Generator):
  NAME = "paramiko"
  URL  = "http://www.lag.net/paramiko/download/paramiko-%s.tar.gz"

  def __init__(self, version):
    super(ParamikioGenerator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.Run(["epydoc", "-o", "docs-babbledrive", "paramiko"], cwd=source)
    self.TakeEpydocOutput(os.path.join(source, "docs-babbledrive"))


def MakeGenerators():
  return [
    ParamikioGenerator("1.7.6"),
  ]
