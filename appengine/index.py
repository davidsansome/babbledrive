from google.appengine.dist import use_library
use_library('django', '1.1')

import os

from django.template import RequestContext
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class IndexPage(webapp.RequestHandler):
  def get(self):
    params = {}

    t = template.load(os.path.join(os.path.dirname(__file__), "index.html"))
    self.response.out.write(t.render(RequestContext(self.request, params)))


application = webapp.WSGIApplication([
  ('/', IndexPage),
], debug=True)


if __name__ == '__main__':
  run_wsgi_app(application)