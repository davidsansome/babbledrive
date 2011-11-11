import generator

import os.path

class Generator(generator.Generator):
  NAME = "httplib2"
  URL  = "https://code.google.com/p/httplib2/"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    source = self.CloneMecurial(self.URL, self.version)

    doc = os.path.join(source, "doc")

    self.Run(["make", "html"], cwd=doc)
    self.TakeSphinxOutput(os.path.join(doc, "html"))


def MakeGenerators():
  return [
    Generator("0.7.1"),
  ]
