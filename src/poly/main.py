import sys
import os
import logging
sys.path.append("src")
import tornado.ioloop
import tornado.web
import tornado.autoreload
import tornado.options
from tornado.options import options, define
from poly.handlers.main import MainHandler
from poly.handlers.twitter_oauth import TwitterHandler, LogoutHandler
from poly.handlers.api.user import ApiUserHandler
from poly.handlers.api.user_list import ApiUserListHandler
from poly.handlers.api.apps import ApiAppsHandler
from poly.stackato.apps import AppsPoller
import poly.mq
import pymongo
import simplejson as json
from simplejson import JSONDecodeError

mongodb_options = {
    "host": "localhost",
    "port": 27017,
    "db": "poly"
}
rabbitmq_options = {
    "host": "127.0.0.1"
}

stackato_services_json = os.environ.get("STACKATO_SERVICES", None)
if stackato_services_json:
    try:
        stackato_services = json.loads(stackato_services_json)
        mongodb_options = stackato_services["poly-db"]
        rabbitmq_options = stackato_services["poly-mq"]
        logging.warn("rabbitmq_options: " + str(rabbitmq_options))
    except JSONDecodeError as e:
        logging.warn("Could not decode STACKATO_SERVICES env. Falling back to default mongodb connection parameters.")

define("listen_port", default=None, help="run on the given port", type=int)

root_dir = os.path.join(os.path.dirname(__file__), "..", "..")
application = tornado.web.Application(
    [
        (r"^/$", MainHandler),
        (r"^/login$", TwitterHandler),
        (r"^/logout$", LogoutHandler),
        (r"^/oauth/twitter", TwitterHandler),
        (r"^/api/user(?:/(?P<twitter_screen_name>[^/\s]+))?$", ApiUserHandler),
        (r"^/api/users$", ApiUserListHandler),
        (r"^/api/apps$", ApiAppsHandler)
    ],
    template_path=os.path.join(root_dir, "templates"),
    static_path=os.path.join(root_dir, "static")
)

if __name__ == "__main__":
    tornado.autoreload.start()
    tornado.options.parse_command_line()

    io_loop = tornado.ioloop.IOLoop.instance()

    application.listen(
        options.listen_port or application.settings["listen_port"],
    )

    application.settings["twitter_consumer_key"] = \
       os.environ.get("TWITTER_CONSUMER_KEY")
    application.settings["twitter_consumer_secret"] = \
        os.environ.get("TWITTER_CONSUMER_SECRET")

    application.settings["cookie_secret"] = "dsisj2ir9fjsifsinmfn232342fdsfqqa"
    application.settings["login_url"] = "/login"

    application.mongo = pymongo.MongoClient(
        host=mongodb_options["host"],
        port=mongodb_options["port"]
    )[mongodb_options["db"]]
    if mongodb_options.has_key("username"):
        application.mongo.authenticate(mongodb_options["username"], mongodb_options["password"])

    logging.info("Connecting to RabbitMQ...")
    mq = poly.mq.Sender(rabbitmq_options, io_loop=io_loop)
    io_loop.add_callback(mq.connect)
    application.io_loop = io_loop
    application.mq = mq
    application.apps_poller = AppsPoller(application)

    print "Starting server"
    io_loop.start()

