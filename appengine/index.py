# System imports
import datetime
import logging
import time
import os
import zipimport

try:
  import json
except ImportError:
  import simplejson as json

# Appengine imports
from google.appengine.api import users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# Local imports
import pyratemp


CONTENT_VERSION  = 4
DEFAULT_PACKAGES = ["python-2.7.1"]
EXPIRATION_SECS = 2419200
LOGGER = logging.getLogger("index")

MIMETYPES = {
  "css":  "text/css",
  "gif":  "image/gif",
  "html": "text/html;charset=utf-8",
  "js":   "application/x-javascript;charset=utf-8",
  "png":  "image/png",
  "sh":   "application/x-sh",
  "text": "text/plain",
  "zip":  "application/zip",
}


class UserInfo(db.Model):
  user              = db.UserProperty(required=True)
  selected_packages = db.StringListProperty(default=DEFAULT_PACKAGES)


class IndexPage(webapp.RequestHandler):
  def get(self):
    user_info = {
      "email":             None,
      "nickname":          None,
      "selected_packages": DEFAULT_PACKAGES,
    }

    # Get the user's information from datastore if he's logged in
    user = users.get_current_user()
    if user:
      user_info["email"]    = user.email()
      user_info["nickname"] = user.nickname()

      query = UserInfo.all()
      query.filter("user =", user)
      record = query.get()

      if record is not None:
        user_info["selected_packages"] = record.selected_packages

    params = {
      "content_version": CONTENT_VERSION,
      "user_info":       json.dumps(user_info),
      "email":           user_info["email"],
      "nickname":        user_info["nickname"],
      "is_logged_in":    user is not None,
      "login_url":       users.create_login_url("/"),
      "logout_url":      users.create_logout_url("/"),
    }

    template_path = os.path.join(os.path.dirname(__file__), "index.html")
    template = pyratemp.Template(filename=template_path, data=params,
      escape=pyratemp.HTML)
    self.response.out.write(template().encode("utf-8"))


class SaveAction(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if not user:
      self.error(403)
      self.response.out.write("Not signed in")
      return

    selected_packages = self.request.get("selected_packages")
    if not selected_packages:
      self.error(400)
      self.response.out.write("Missing 'selected_packages' field")
      return

    try:
      selected_packages = json.loads(selected_packages)
    except ValueError, e:
      self.error(400)
      self.response.out.write("Invalid JSON in 'selected_packages' field")
      return

    # Get the user if he already exists
    query = UserInfo.all()
    query.filter("user =", user)
    record = query.get()

    # Otherwise create one
    if record is None:
      record = UserInfo(user=user)

    # Update the selected packages field
    record.selected_packages = selected_packages
    record.put()


class LoadZippedPage(webapp.RequestHandler):
  def get(self, package, filename):
    for bad_char in "-./":
      package = package.replace(bad_char, "_")

    path = os.path.join(os.path.dirname(__file__), package + ".zip")

    LOGGER.info("Opening file '%s' from zip file '%s'", filename, path)

    # Open the zip file
    try:
      zipfile = zipimport.zipimporter(path)
    except zipimport.ZipImportError:
      self.error(404)
      return

    # Get the file out
    try:
      data = zipfile.get_data(filename)
    except IOError:
      self.error(404)
      return

    # Write headers
    self.response.headers["Cache-Control"] = "public, max-age=%d" % EXPIRATION_SECS

    expires = datetime.datetime.fromtimestamp(time.time() + EXPIRATION_SECS)
    self.response.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

    extension = filename.split('.')[-1]
    if extension in MIMETYPES:
      self.response.headers["Content-Type"] = MIMETYPES[extension]
    else:
      self.response.headers["Content-Type"] = "application/octet-stream"

    # Write data
    self.response.out.write(data)


application = webapp.WSGIApplication([
  ('/', IndexPage),
  ('/api/save', SaveAction),
  ('/static/doc/([^/]*)/(.*)', LoadZippedPage),
], debug=True)


if __name__ == '__main__':
  run_wsgi_app(application)
