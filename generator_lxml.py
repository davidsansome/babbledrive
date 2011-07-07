import generator

import os.path

class Generator(generator.Generator):
  NAME = "lxml"
  URL  = "http://pypi.python.org/packages/source/l/lxml/lxml-%s.tar.gz"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.Run(["python", "setup.py", "build", "--with-xslt-config=/usr/bin/xslt-config"], cwd=source)
    self.Run(["make", "apihtml"], cwd=source)
    self.TakeEpydocOutput(os.path.join(source, "doc/html/api"))


def MakeGenerators():
  return [
    Generator("2.3"),
  ]
