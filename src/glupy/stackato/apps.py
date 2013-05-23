
import os.path
import yaml
import logging
import functools
from datetime import timedelta
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import simplejson as json
from simplejson import JSONDecodeError


class AppsPoller():

    def __init__(self, application):

        self.poll_delay = timedelta(seconds=3)

        cluster_yml_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'clusters.yml')
        self.clusters = yaml.load(file(cluster_yml_path, 'r'))

        self.application = application
        self.http_client = AsyncHTTPClient()

        self.apps = {}
        for cluster in self.clusters:
            self.apps[cluster["target"]] = []
            self.get_apps(cluster)

    def get_apps(self, cluster):
        for cluster in self.clusters:
            apps_api = "http://" + cluster["target"] + "/apps"
            headers = {
                "Authorization": cluster["auth_token"]
            }
            logging.warn("Fetching apps from " + str(apps_api))
            self.http_client.fetch(
                HTTPRequest(apps_api, headers=headers),
                functools.partial(
                    self.got_apps,
                    cluster
                )
            )

    def got_apps(self, cluster, response):
        if response and response.code == 200:
            logging.warn("response from " + cluster["target"])
            try:
                apps = json.loads(response.body)
                self.apps[cluster["target"]] = apps
            except JSONDecodeError as e:
                logging.error(
                    "Failed to decode JSON response from " +
                    cluster["target"] +
                    str(e)
                )
        else:
            logging.error(
                "Failed to fetch from " +
                cluster["target"] +
                str(response)
            )
        self.application.io_loop.add_timeout(
            self.poll_delay,
            functools.partial(
                self.get_apps,
                cluster
            )
        )

