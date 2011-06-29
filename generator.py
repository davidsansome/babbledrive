import glob
import json
import logging
import operator
import os
import os.path
import pickle
import re
import shutil
import subprocess
import sys
import tarfile
import urllib2
import zipfile
import zlib

class GeneratorError(Exception):
  pass


class Generator(object):
  OUTPUT_DATA = "appengine/static/data/%s-%s.js"
  OUTPUT_ZIP  = "appengine/%s.zip"

  EPYDOC_MAGIC = "@@BABBLEDRIVE_NAMEVERSION@@"

  SPHINX_V2_MARKER   = "# Sphinx inventory version 2"
  SPHINX_ZLIB_MARKER = "# The remainder of this file is compressed using zlib.\n"

  TYPES = {
    # Sphinx version 1
    "mod": 0,
    "class": 1,
    "exception": 2,
    "ctype": 3,
    "cmacro": 4,
    "classmethod": 5,
    "function": 6,
    "method": 7,
    "cfunction": 8,
    "data": 9,
    "attribute": 10,
    "cvar": 11,
    "cmember": 12,

    # Sphinx version 2
    "py:module": 0,
    "py:class": 1,
    "py:exception": 2,
    "py:staticmethod": 5,
    "py:classmethod": 5,
    "py:function": 6,
    "py:method": 7,
    "py:data": 9,
    "py:attribute": 10,
  }

  PYDOCTOR_TYPES = {
    "Package": 0,
    "Module": 0,
    "Class": 1,
    "Interface": 1,
    "Class Method": 5,
    "Static Method": 5,
    "Function": 6,
    "Method": 7,
    "Attribute": 10,
  }

  # Set by main.py
  OPTIONS = None

  def __init__(self, name, version):
    self.name = name
    self.version = version
    self.logger = logging.getLogger("generator.%s-%s" % (name, version))

    self.cwd = os.path.dirname(__file__)

    # Get the environment
    self._env = dict(os.environ)
    path = self._env.get("PATH", "").split(":")
    pythonpath = self._env.get("PYTHONPATH", "").split(":")

    # Add epydoc paths to the environment
    epydoc = os.path.join(self.cwd, "generator-epydoc")
    path.insert(0, os.path.join(epydoc, "scripts"))
    pythonpath.insert(0, epydoc)

    # Add pydoctor paths to the environment
    pydoctor = os.path.join(self.cwd, "generator-pydoctor")
    path.insert(0, os.path.join(pydoctor, "bin"))
    pythonpath.insert(0, pydoctor)

    self._env["PATH"] = ":".join(path)
    self._env["PYTHONPATH"] = ":".join(pythonpath)

    # pydoctor goes on our own pythonpath too
    sys.path.insert(0, pydoctor)

    # Create the downloads directory
    self.downloads = os.path.join(self.cwd, "_downloads")

    # Create the working directory for this package
    self.work = os.path.join(self.cwd, "_work/%s-%s" % (name, version))
    if os.path.exists(self.work):
      shutil.rmtree(self.work)
    os.makedirs(self.work)

    # Output directories
    self.safe_name = "%s_%s" % (name, version)
    for bad_char in "-.":
      self.safe_name = self.safe_name.replace(bad_char, "_")

    self.output_data = os.path.join(self.cwd, self.OUTPUT_DATA % (name, version))
    self.output_zip  = os.path.join(self.cwd, self.OUTPUT_ZIP  % self.safe_name)

  def AdjustSphinxConf(self, filename):
    contents = open(filename).read()
    contents += '\nhtml_theme="sphinx-theme"' + \
                '\nhtml_theme_path=["%s"]\n' % \
                    os.path.join(self.cwd, "generator-sphinx")

    contents = re.sub(r'html_use_opensearch .*', '', contents)

    open(filename, 'w').write(contents)

  def DownloadSource(self, url):
    self.logger.info("downloading %s" % url)

    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    handle = opener.open(url)

    actual_url = handle.geturl()
    filename = actual_url[actual_url.rindex("/")+1:]
    path = os.path.join(self.downloads, filename)

    if not os.path.exists(self.downloads):
      os.makedirs(self.downloads)

    if os.path.exists(path):
      self.logger.info("already exists, not redownloading %s" % path)
    else:
      self.logger.info("saving %s" % path)
      open(path, 'w').write(handle.read())

    handle.close()

    return path

  def ExtractSource(self, path):
    self.logger.info("extracting %s" % path)

    tar = tarfile.open(path)
    directory = tar.getnames()[0].split('/')[0]
    tar.extractall(self.work)
    tar.close()

    return os.path.join(self.work, directory)

  def Run(self, args, **kwargs):
    self.logger.info("running %s" % " ".join(args))

    kwargs.update({
      "env":    self._env,
    })

    if not self.OPTIONS.verbose:
      kwargs.update({
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
      })

    handle = subprocess.Popen(args, **kwargs)
    stdout = handle.communicate()[0]

    if handle.returncode != 0:
      if not self.OPTIONS.verbose:
        print >> sys.stderr, stdout

      raise GeneratorError("Command '%s' exited with status %d" % (
        args[0], handle.returncode))

  def RunPydoctor(self, project_name, project_url, packages, system_class=None,
                  html_viewsource_base=None, **kwargs):
    args = ["pydoctor",
      "--project-name", project_name,
      "--project-url", project_url,
      "--html-output", "babbledrive-apidocs",
      "--project-base-dir", kwargs["cwd"],
      "--output-pickle", "babbledrive-pickle",
      "--quiet", "--make-html",
    ]

    for package in packages:
      args += ["--add-package", package]

    if system_class is not None:
      args += ["--system-class", system_class]

    if html_viewsource_base is not None:
      args += ["--html-viewsource-base", html_viewsource_base]

    self.Run(args, **kwargs)

  def TakeEpydocOutput(self, path):
    self.logger.info("taking epydoc output from %s" % path)

    babbledrive_data = os.path.join(path, "babbledrive-data.js")
    if not os.path.exists(babbledrive_data):
      raise GeneratorError("The generated file '%s' was not found" % babbledrive_data)

    # Replace the magic string in the babbledrive data file
    data = open(babbledrive_data).read()
    data = data.replace(self.EPYDOC_MAGIC, "%s-%s" % (self.name, self.version))
    open(babbledrive_data, 'w').write(data)

    # Replace references to epydoc.css or epydoc.js in the html files
    for filename in glob.glob(os.path.join(path, "*.html")):
      data = open(filename).read()
      data = re.sub(r'(epydoc.(css|js))', r'../../\1', data)
      data = re.sub(r'(crarr.png)', r'../../images/\1', data)
      open(filename, 'w').write(data)

    # Remove shared files
    for filename in ["epydoc.css", "epydoc.js", "crarr.png"]:
      filepath = os.path.join(path, filename)
      if os.path.exists(filepath):
        os.remove(filepath)

    self._RemoveOldOutput()
    self._TakeData(babbledrive_data)
    self._TakeDocs(path)

  def _RemoveOldOutput(self):
    self.logger.info("removing old data")
    if os.path.exists(self.output_data):
      os.remove(self.output_data)
    if os.path.exists(self.output_zip):
      os.remove(self.output_zip)

  def _TakeData(self, path):
    self.logger.info("installing %s" % self.output_data)
    shutil.move(path, self.output_data)

  def _TakeDocs(self, path):
    self.logger.info("archiving %s to %s" % (path, self.output_zip))
    output = zipfile.ZipFile(self.output_zip, 'w', zipfile.ZIP_DEFLATED)

    for dirpath, dirnames, filenames in os.walk(path):
      for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        relpath = os.path.relpath(filepath, path)
        output.write(filepath, relpath)

    output.close()

  def TakeSphinxOutput(self, path):
    self.logger.info("taking sphinx output from %s" % path)

    objects_inv = os.path.join(path, "objects.inv")
    if not os.path.exists(objects_inv):
      raise GeneratorError("The generated file '%s' was not found" % objects_inv)

    # Process the objects.inv file
    data = open(objects_inv).read()
    items = []

    is_v2 = self.SPHINX_V2_MARKER in data

    # Decompress the data inside if it's compressed
    if self.SPHINX_ZLIB_MARKER in data:
      start = data.index(self.SPHINX_ZLIB_MARKER) + len(self.SPHINX_ZLIB_MARKER)
      data = zlib.decompress(data[start:])

    # Process each line
    for line in data.split("\n"):
      line = line.strip()
      if not line or line.startswith("#") or " std:" in line:
        continue

      fields = line.split(" ")
      name = fields[0]

      # Map the type to a number
      try:
        type_index = self.TYPES[fields[1]]
      except KeyError:
        raise GeneratorError("Unknown sphinx type '%s' in line '%s'" % (
          fields[1], line))

      if type_index is None:
        # Ignore this line
        continue

      # Get a destination URL
      if not is_v2:
        if fields[1] == "mod":
          destination = "%s#module-%s" % (fields[2], name)
        else:
          destination = "%s#%s" % (fields[2], name)
      else:
        destination = fields[3].replace('$', name)

      # Add the item to the list
      items.append([name.lower(), name, type_index, destination])

    # Sort the list by name
    items = sorted(items, key=operator.itemgetter(0))

    self._RemoveOldOutput()
    self._TakeDocs(path)

    # Write out the data file
    self.logger.info("installing %s" % self.output_data)
    output_file = open(self.output_data, 'w')
    output_file.write('library.register_package_data("%s-%s",%s);' % (
      self.name, self.version, json.dumps(items, separators=(',', ':'))))
    output_file.close()

  def TakePydoctorOutput(self, path):
    self.logger.info("taking pydoctor output from %s" % path)

    pickle_path = os.path.join(path, "babbledrive-pickle")
    html_path   = os.path.join(path, "babbledrive-apidocs")
    system = pickle.load(open(pickle_path))

    items = []
    for o in system.allobjects.values():
      name = o.fullName()
      type_index = self.PYDOCTOR_TYPES[o.kind]

      if o.kind == "Class" and "Exception" in o.bases:
        type_index = 2

      if o.kind in ["Method", "Function"]:
        url = "%s.html#%s" % (o.parent.fullName(), o.name)
      else:
        url = "%s.html" % name

      items.append([name.lower(), name, type_index, url])

    # Sort the list by name
    items = sorted(items, key=operator.itemgetter(0))

    self._RemoveOldOutput()
    self._TakeDocs(html_path)

    # Write out the data file
    self.logger.info("installing %s" % self.output_data)
    output_file = open(self.output_data, 'w')
    output_file.write('library.register_package_data("%s-%s",%s);' % (
      self.name, self.version, json.dumps(items, separators=(',', ':'))))
    output_file.close()

  def Generate(self):
    raise NotImplementedError()
