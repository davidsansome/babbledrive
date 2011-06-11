import logging
import os
import os.path
import shutil
import subprocess
import tarfile
import urllib
import urllib2

class GeneratorError(Exception):
  pass


class Generator(object):
  OUTPUT_DATA = "appengine/static/data/%s-%s.js"
  OUTPUT_DOC  = "appengine/static/doc/%s-%s"

  EPYDOC_MAGIC = "@@BABBLEDRIVE_NAMEVERSION@@"

  def __init__(self, name, version):
    self.name = name
    self.version = version
    self.logger = logging.getLogger("generator.%s-%s" % (name, version))

    cwd = os.path.dirname(__file__)

    # Get the environment
    self._env = dict(os.environ)
    path = self._env.get("PATH", "").split(":")
    pythonpath = self._env.get("PYTHONPATH", "").split(":")

    # Add epydoc paths to the environment
    epydoc = os.path.join(cwd, "generator-epydoc")
    path.insert(0, os.path.join(epydoc, "scripts"))
    pythonpath.insert(0, epydoc)

    self._env["PATH"] = ":".join(path)
    self._env["PYTHONPATH"] = ":".join(pythonpath)

    # Create the working directory for this package
    self.work = os.path.join(cwd, "_%s-%s" % (name, version))
    if os.path.exists(self.work):
      shutil.rmtree(self.work)
    os.mkdir(self.work)

    # Output directories
    self.output_data = os.path.join(cwd, self.OUTPUT_DATA % (name, version))
    self.output_doc  = os.path.join(cwd, self.OUTPUT_DOC  % (name, version))

  def DownloadSource(self, url):
    self.logger.info("downloading %s" % url)

    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    handle = opener.open(url)

    actual_url = handle.geturl()
    filename = actual_url[actual_url.rindex("/")+1:]
    path = os.path.join(self.work, filename)

    self.logger.info("saving %s" % path)
    open(path, 'w').write(handle.read())

    return path

  def ExtractSource(self, path):
    self.logger.info("extracting %s" % path)

    tar = tarfile.open(path)
    firstname = tar.getnames()[0]
    tar.extractall(self.work)
    tar.close()

    return os.path.join(self.work, firstname)

  def Run(self, args, **kwargs):
    self.logger.info("running %s" % " ".join(args))

    kwargs["env"] = self._env

    handle = subprocess.Popen(args, **kwargs)
    handle.wait()

    if handle.returncode != 0:
      raise GeneratorError("Command '%s' exited with status %d" % (
        args[0], handle.returncode))

  def TakeEpydocOutput(self, path):
    babbledrive_data = os.path.join(path, "babbledrive-data.js")
    if not os.path.exists(babbledrive_data):
      raise GeneratorError("The generated file '%s' was not found" % babbledrive_data)

    # Replace the magic string in the babbledrive data file
    data = open(babbledrive_data).read()
    data = data.replace(self.EPYDOC_MAGIC, "%s-%s" % (self.name, self.version))
    open(babbledrive_data, 'w').write(data)

    # Remove old output
    self.logger.info("removing old data")
    if os.path.exists(self.output_data):
      os.remove(self.output_data)
    if os.path.exists(self.output_doc):
      shutil.rmtree(self.output_doc)

    # Copy new files
    self.logger.info("installing %s" % self.output_data)
    shutil.move(babbledrive_data, self.output_data)

    self.logger.info("installing %s" % self.output_doc)
    shutil.move(path, self.output_doc)

  def Generate(self):
    raise NotImplementedError()
