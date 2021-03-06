import generator

import os.path

class Generator(generator.Generator):
  NAME = "pyinotify"
  URL  = "https://github.com/seb-m/pyinotify/tarball/%s"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    if os.path.exists(os.path.join(source, "python2")):
      source = os.path.join(source, "python2")

    self.Run(["make"], cwd=source)
    self.TakeEpydocOutput(os.path.join(source, "docstrings"))


def MakeGenerators():
  return [
    Generator("0.8.3"),
    Generator("0.9.2"),
  ]
