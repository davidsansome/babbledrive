import generator

import os.path

class Generator(generator.Generator):
  NAME = "ipaddr"
  URL  = "http://ipaddr-py.googlecode.com/files/ipaddr-%s.tar.gz"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.Run(["epydoc", "-o", "docs-babbledrive", "ipaddr"], cwd=source)
    self.TakeEpydocOutput(os.path.join(source, "docs-babbledrive"))


def MakeGenerators():
  return [
    Generator("2.1.9"),
  ]
