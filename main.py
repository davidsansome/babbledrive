import glob
import logging
import optparse
import sys

def main():
  # Initialise logging
  logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(name)-32s %(message)s",
  )

  logger = logging.getLogger("main")

  # Parse options
  parser = optparse.OptionParser()
  options, args = parser.parse_args(sys.argv[1:])

  package_name = None
  package_version = None

  if len(args) >= 1:
    package_name = args[0]
  if len(args) >= 2:
    package_version = args[1]

  # Find generator modules
  module_filenames = glob.glob("generator_*.py")
  generators = []

  # Load generator modules
  for filename in module_filenames:
    logger.info("loading generators from %s" % filename)

    module_name = filename[:-3]

    module = __import__(module_name)
    generators += module.MakeGenerators()

  # Run them
  for generator in generators:
    if (package_name is not None and generator.name != package_name) or \
       (package_version is not None and generator.version != package_version):
      logger.info("skipping %s-%s" % (generator.name, generator.version))
      continue

    generator.Generate()


if __name__ == "__main__":
  main()

