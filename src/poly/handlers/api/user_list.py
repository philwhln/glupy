
import re
from poly.handlers.auth import AuthHandler
import simplejson as json
import tornado.web
import logging
from pymongo import ASCENDING, DESCENDING

class ApiUserListHandler(AuthHandler, tornado.auth.TwitterMixin):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, user_type=None):
        logged_in_user_screen_name = self.get_current_user()
        logged_in_user = self.application.mongo["user"].find_one({ "twitter.screen_name": logged_in_user_screen_name })
        twitter_access_token = logged_in_user["twitter"]["access_token"]

        sort_field = self.get_argument("sort_field", None)
        if not sort_field:
            sort_field = "twitter.screen_name"
        if self.get_argument("sort_order", None) == "descending":
            sort_order = DESCENDING
        else:
            sort_order = ASCENDING

        query = {}
        for search_field in ["name", "screen_name", "location", "description"]:
            search_term = self.get_argument("search.twitter." + search_field, None)
            if (search_term):
                query["twitter." + search_field] = re.compile(search_term, re.IGNORECASE)

        cursor = self.application.mongo["user"].find(
            query,
            fields={
                "_id": False,
                "twitter.screen_name": True,
                "twitter.name": True,
                "twitter.location": True,
                "twitter.friends_count": True,
                "twitter.followers_count": True,
                "twitter.description": True,
                "twitter.profile_image_url": True,
                "twitter.url": True
            },
            sort=[(sort_field, sort_order)]
        )
        response = {
           "total": cursor.count(),
           "list": list(cursor[0:50])
        }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(response, indent=True))
        self.finish()

