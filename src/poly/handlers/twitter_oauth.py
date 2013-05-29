
import tornado.web
import tornado.auth

class TwitterHandler(tornado.web.RequestHandler,
                     tornado.auth.TwitterMixin):

    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()

    def _on_auth(self, twitter_user):
        if not twitter_user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")

        existing = self.application.mongo["user"].find_one({ "twitter.id": twitter_user["id"] })
        if existing:
            # update the user account
            self.application.mongo["user"].update(
                { "_id": existing["_id"] },
                { "$set": { "twitter": twitter_user } }
            )
        else:
            # create user account
            self.application.mongo["user"].insert({
                "twitter": twitter_user
            })

        user_cookie = {
            "screen_name": twitter_user["screen_name"]
        }
            
        self.set_secure_cookie("user", tornado.escape.json_encode(user_cookie))
        self.redirect("/")

class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")
