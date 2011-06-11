import generator

import os.path

class DbusGenerator(generator.Generator):
  NAME = "dbus-python"
  URL  = "http://dbus.freedesktop.org/releases/dbus-python/dbus-python-%s.tar.gz"

  def __init__(self, version):
    super(DbusGenerator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.Run(["./configure", "--enable-api-docs"], cwd=source)
    self.Run(["make", "-j8", "api"], cwd=source)
    self.TakeEpydocOutput(os.path.join(source, "api"))


def MakeGenerators():
  return [
    DbusGenerator("0.84.0"),
  ]
