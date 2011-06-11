import generator

import os.path

class SimplejsonGenerator(generator.Generator):
  NAME = "simplejson"
  URL  = "http://pypi.python.org/packages/source/s/simplejson/simplejson-%s.tar.gz"

  def __init__(self, version):
    super(SimplejsonGenerator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.AdjustSphinxConf(os.path.join(source, "conf.py"))
    self.Run(["python", "scripts/make_docs.py"], cwd=source)
    self.TakeSphinxOutput(os.path.join(source, "docs"))


def MakeGenerators():
  return [
    SimplejsonGenerator("2.1.6"),
  ]
