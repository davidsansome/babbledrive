import generator

import os.path

class MysqlpythonGenerator(generator.Generator):
  NAME = "mysql-python"
  URL  = "http://pypi.python.org/packages/source/M/MySQL-python/MySQL-python-%s.tar.gz"

  def __init__(self, version):
    super(MysqlpythonGenerator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % self.version)
    source = self.ExtractSource(tarball)

    self.Run(["epydoc", "-o", "docs-babbledrive", "MySQLdb"], cwd=source)
    self.TakeEpydocOutput(os.path.join(source, "docs-babbledrive"))


def MakeGenerators():
  return [
    MysqlpythonGenerator("1.2.3"),
  ]
