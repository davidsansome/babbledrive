import glob
import logging
import optparse
import sys

import generator

USAGE = "%prog [-v] [<package> [<version]]"

def main():
  # Initialise logging
  logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(name)-32s %(message)s",
  )

  logger = logging.getLogger("main")

  # Parse options
  parser = optparse.OptionParser(usage=USAGE)
  parser.add_option("-v", "--verbose", dest="verbose", action="store_true")
  options, args = parser.parse_args(sys.argv[1:])

  package_name = None
  package_version = None

  if len(args) >= 1:
    package_name = args[0]
  if len(args) >= 2:
    package_version = args[1]

  generator.Generator.OPTIONS = options

  # Find generator modules
  module_filenames = glob.glob("generator_*.py")
  generators = []

  # Load generator modules
  for filename in module_filenames:
    module_name = filename[:-3]

    module = __import__(module_name)
    generators += module.MakeGenerators()

  # Run them
  for gen in generators:
    if (package_name is not None and gen.name != package_name) or \
       (package_version is not None and gen.version != package_version):
      continue

    gen.Generate()


if __name__ == "__main__":
  main()

