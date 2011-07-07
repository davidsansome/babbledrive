import generator

import os.path

class Generator(generator.Generator):
  NAME = "twisted"
  URL  = "http://pypi.python.org/packages/source/T/Twisted/Twisted-%s.tar.bz2"

  def __init__(self, version):
    super(Generator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.RunPydoctor("Twisted", "http://twistedmatrix.com/", ["twisted"],
      "pydoctor.twistedmodel.TwistedSystem",
      "http://twistedmatrix.com/trac/browser/tags/releases/twisted-11.0.0",
      cwd=source)
    self.TakePydoctorOutput(source)


def MakeGenerators():
  return [
    Generator("11.0.0"),
  ]
