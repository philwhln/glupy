
from glupy.handlers.auth import AuthHandler
import tornado.web

class MainHandler(AuthHandler):

    def get(self):
        self.render(
            "index.html",
            user_id=self.get_current_user(),
            app_clusters=self.application.apps_poller.apps
        )

