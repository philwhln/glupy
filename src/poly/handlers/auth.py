
import tornado.web
import simplejson as json

class AuthHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        screen_name = None
        user_json = self.get_secure_cookie("user")
        if user_json:
            user_cookie = json.loads(user_json)
            if user_cookie and user_cookie.has_key("screen_name"):
                screen_name = user_cookie["screen_name"]
        return screen_name

