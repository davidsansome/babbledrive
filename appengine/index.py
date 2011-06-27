# System imports
import os

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


CONTENT_VERSION  = 3
DEFAULT_PACKAGES = ["python-2.7.1"]


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


application = webapp.WSGIApplication([
  ('/', IndexPage),
  ('/api/save', SaveAction),
], debug=True)


if __name__ == '__main__':
  run_wsgi_app(application)
