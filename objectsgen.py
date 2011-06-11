import json
import operator
import sys

TYPES = [
  "mod", "class", "exception", "ctype",
  "cmacro",
  "classmethod", "function", "method", "cfunction",
  "data", "attribute", "cvar", "cmember",
]

def modanchor(x):
  if x[2] == "mod":
    x[3] = "%s#module-%s" % (x[3], x[1])
  else:
    x[3] = "%s#%s" % (x[3], x[1])
  return x


if len(sys.argv) != 3:
  print >> sys.stderr, "Usage: %s <nameversion> <objects.inv>" % sys.argv[0]
  sys.exit(1)

# Read the file, remove comments, strip each line and split on whitespace
items = [x.strip().split(" ") for x in open(sys.argv[2]) if not x.startswith("#")]

# Add a lowercase version of the name
items = [[x[0].lower()] + x for x in items]

# Add the anchor on to the end of the URL
items = [modanchor(x) for x in items]

# Convert the type to a number
items = [[x[0], x[1], TYPES.index(x[2]), x[3]] for x in items]

# Sort
items = sorted(items, key=operator.itemgetter(0))

print 'library.register_package_data("%s",%s);' % (
  sys.argv[1], json.dumps(items, separators=(',', ':')))
