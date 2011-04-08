import json
import operator
import sys

ORDER = [
  "mod", "class", "exception", "ctype",
  "cmacro",
  "classmethod", "function", "method", "cfunction",
  "data", "attribute", "cvar", "cmember",
]

def sortkey(x):
  return ORDER.index(x[1])

items = [x.strip().split(" ") for x in open(sys.argv[1]) if not x.startswith("#")]
items = sorted(items, key=operator.itemgetter(0))
items = sorted(items, key=sortkey)

print "data=" + json.dumps(items, separators=(',', ':'))
