import generator

import os.path

class SqlalchemyGenerator(generator.Generator):
  NAME = "sqlalchemy"
  URL  = "http://pypi.python.org/packages/source/S/SQLAlchemy/SQLAlchemy-%s.tar.gz"

  def __init__(self, version):
    super(SqlalchemyGenerator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    doc = os.path.join(source, "doc/build")

    self.AdjustSphinxConf(os.path.join(doc, "conf.py"))
    self.Run(["make", "html"], cwd=doc)
    self.TakeSphinxOutput(os.path.join(doc, "output/html"))


def MakeGenerators():
  return [
    SqlalchemyGenerator("0.7.1"),
  ]
