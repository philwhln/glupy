
from poly.handlers.auth import AuthHandler
import simplejson as json
from simplejson import JSONDecodeError
import tornado.web
import tornado.gen
import logging
from time import sleep

class ApiUserHandler(AuthHandler, tornado.auth.TwitterMixin):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, twitter_screen_name=None, component=None):
        logged_in_user_id = self.get_current_user()
        logged_in_user = self.application.mongo["user"].find_one({ "twitter.id": logged_in_user_id })
        twitter_access_token = logged_in_user["twitter"]["access_token"]
        if not twitter_screen_name:
            user = logged_in_user
            twitter_screen_name = logged_in_user["twitter"]["screen_name"]
        else:
            user = self.application.mongo["user"].find_one({ "twitter.screen_name": twitter_screen_name })
            if not user:
                logging.info("twitter api call /users/show.json")
                twitter_user = yield self.twitter_request(
                    "http://api.twitter.com/1/users/show.json",
                    access_token=twitter_access_token,
                    screen_name=twitter_screen_name
                )
                if twitter_user:
                    user = { "twitter": twitter_user }
                    self.application.mongo["user"].insert({
                        "twitter": twitter_user
                    })
        if not user:
            self.send_error(404)
        else:
            yield self.fetch_twitter_follower_ids(user, twitter_access_token, twitter_screen_name)
            self.set_header("Content-Type", "application/json")
            if user.has_key("_id"):
                del user["_id"]
            self.write(json.dumps(user, indent=True))
            self.finish()

    @tornado.gen.coroutine
    def fetch_twitter_follower_ids(self, user, twitter_access_token, twitter_screen_name):
        for attr_type in ["follower", "friend"]:
            ids = user.get("twitter", {}).get( attr_type + "_ids" , None)
            if not ids:
                cursor = -1
                ids = []
                while cursor != 0:
                    logging.info("twitter api call " + attr_type + "s/ids.json")
                    response = yield self.twitter_request(
                        "http://api.twitter.com/1.1/" + attr_type + "s/ids.json",
                        access_token=twitter_access_token,
                        screen_name=twitter_screen_name,
                    )
                    ids += response["ids"]
                    cursor = response["next_cursor"]
                    user["twitter"][ attr_type + "_ids" ] = ids
                    # save ids list to db
                    updates = { "$set": { "twitter." + attr_type + "_ids": ids } }
                    if cursor == 0:
                        # reached the end. delete cursor, since not needed
                        updates.setdefault("$unset", {})["twitter." + attr_type + "_ids_next_cursor"] = 1
                    else:
                        # save next cursor, so we can continue later if we hit exception
                        updates["$set"]["twitter." + attr_type + "_ids_next_cursor"] = cursor
                    # update db everytime, encase we hit an exception
                    self.application.mongo["user"].update(
                        { "twitter.screen_name": twitter_screen_name },
                        updates
                    )
                    # sleep for 1 second. note, will block event-loop
                    sleep(1)

    @tornado.web.authenticated
    def post(self, twitter_screen_name=None, component=None):
        post_data = None
        try:
            post_data = json.loads(self.request.body)
        except JSONDecodeError as e:
            return self.send_error(400)
        updates = {}
        for attr_name in ["is_seed", "is_lead"]:
            attr_value = post_data.get(attr_name, None)
            if attr_value != None:
                if attr_value == True:
                    updates.setdefault("$set", {})[attr_name] = attr_value
                elif attr_value == False:
                    updates.setdefault("$unset", {})[attr_name] = 1
        if updates:
            self.application.mongo["user"].update(
                { "twitter.screen_name": twitter_screen_name },
                updates
            )

