import generator

import os.path

class Generator(generator.Generator):
  NAME = "django"
  URL  = "http://www.djangoproject.com/download/%s/tarball/"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    doc = os.path.join(source, "docs")

    self.Run(["make", "html"], cwd=doc)
    self.TakeSphinxOutput(os.path.join(doc, "_build/html"))


def MakeGenerators():
  return [
    Generator("1.3"),
  ]
