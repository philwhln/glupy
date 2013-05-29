
from poly.handlers.auth import AuthHandler
import simplejson as json
import tornado.web

class ApiAppsHandler(AuthHandler):

    @tornado.web.authenticated
    def get(self):
        self.write(
            json.dumps(
                self.application.apps_poller.apps,
                indent=True
            )
        )

