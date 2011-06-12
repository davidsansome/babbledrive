import glob
import json
import logging
import operator
import os
import os.path
import re
import shutil
import subprocess
import tarfile
import urllib2
import zlib

class GeneratorError(Exception):
  pass


class Generator(object):
  OUTPUT_DATA = "appengine/static/data/%s-%s.js"
  OUTPUT_DOC  = "appengine/static/doc/%s-%s"

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
    "std:label": None,
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

    self._env["PATH"] = ":".join(path)
    self._env["PYTHONPATH"] = ":".join(pythonpath)

    # Create the downloads directory
    self.downloads = os.path.join(self.cwd, "_downloads")

    # Create the working directory for this package
    self.work = os.path.join(self.cwd, "_work/%s-%s" % (name, version))
    if os.path.exists(self.work):
      shutil.rmtree(self.work)
    os.makedirs(self.work)

    # Output directories
    self.output_data = os.path.join(self.cwd, self.OUTPUT_DATA % (name, version))
    self.output_doc  = os.path.join(self.cwd, self.OUTPUT_DOC  % (name, version))

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
    firstname = tar.getnames()[0]
    tar.extractall(self.work)
    tar.close()

    return os.path.join(self.work, firstname)

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

    # Remove old output
    self.logger.info("removing old data")
    if os.path.exists(self.output_data):
      os.remove(self.output_data)
    if os.path.exists(self.output_doc):
      shutil.rmtree(self.output_doc)

    # Move new files
    self.logger.info("installing %s" % self.output_data)
    shutil.move(babbledrive_data, self.output_data)

    self.logger.info("installing %s" % self.output_doc)
    shutil.move(path, self.output_doc)

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
      if not line or line.startswith("#"):
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

    # Remove old output
    self.logger.info("removing old data")
    if os.path.exists(self.output_data):
      os.remove(self.output_data)
    if os.path.exists(self.output_doc):
      shutil.rmtree(self.output_doc)

    # Write out the data file
    self.logger.info("installing %s" % self.output_data)
    output_file = open(self.output_data, 'w')
    output_file.write('library.register_package_data("%s-%s",%s);' % (
      self.name, self.version, json.dumps(items, separators=(',', ':'))))
    output_file.close()

    # Move everything else
    self.logger.info("installing %s" % self.output_doc)
    shutil.move(path, self.output_doc)

  def Generate(self):
    raise NotImplementedError()
