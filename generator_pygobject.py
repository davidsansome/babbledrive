import generator

import os.path

class Generator(generator.Generator):
  NAME = "pygobject"
  URL  = "http://ftp.gnome.org/pub/GNOME/sources/pygobject/%s/pygobject-%s.tar.bz2"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % (
      ".".join(self.version.split(".")[:2]), self.version))
    source = self.ExtractSource(tarball)

    self.TakeDevhelpOutput(os.path.join(source, "docs/html"))


def MakeGenerators():
  return [
    Generator("2.28.6"),
  ]
