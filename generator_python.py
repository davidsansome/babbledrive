import generator

import os.path

class Generator(generator.Generator):
  NAME = "python"
  URL  = "http://www.python.org/ftp/python/%s/Python-%s.tar.bz2"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % (self.version, self.version))
    source = self.ExtractSource(tarball)

    doc = os.path.join(source, "Doc")

    self.AdjustSphinxConf(os.path.join(doc, "conf.py"))
    self.Run(["make", "html"], cwd=doc)
    self.TakeSphinxOutput(os.path.join(doc, "build/html"))


def MakeGenerators():
  return [
    Generator("2.7.1"),
  ]
