import generator

import glob
import os.path

class TkinterGenerator(generator.Generator):
  NAME = "tkinter"
  URL  = "http://www.python.org/ftp/python/%s/Python-%s.tar.bz2"

  def __init__(self, version):
    super(TkinterGenerator, self).__init__(self.NAME, version)

  def Generate(self):
    tarball = self.DownloadSource(self.URL % (self.version, self.version))
    source = self.ExtractSource(tarball)

    # Get the list of Tkinter modules
    lib_tk_dir = os.path.join(source, "Lib/lib-tk")
    py_files = glob.glob(os.path.join(lib_tk_dir, "*.py"))
    modules = [os.path.basename(x)[:-3] for x in py_files]

    self.Run(["epydoc"] + modules, cwd=lib_tk_dir)
    self.TakeEpydocOutput(os.path.join(lib_tk_dir, "html"))


def MakeGenerators():
  return [
    TkinterGenerator("2.7.1"),
  ]
