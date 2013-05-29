
import logging
import socket
import time
import simplejson as json

import pika
from pika.adapters.tornado_connection import TornadoConnection

class Sender(object):
    def __init__(self, settings, io_loop):
        self.io_loop = io_loop
        self.channel = None
        self.exchange = "poly"

        credentials = None
        if settings.get("username", None):
            credentials = pika.PlainCredentials(
                settings["username"],
                settings["password"]
            )
        self.connection_parameters = None
        if credentials or settings.get("host", None) or settings.get("vhost"):
            self.connection_parameters = pika.ConnectionParameters(
                credentials=credentials,
                host=settings.get("host", None),
                port=settings.get("port", None),
                virtual_host=settings.get("vhost", None)
            )
        else:
            raise Exception("NO self.connection_parameters")
        self.settings = settings

    def connect(self):
        logging.info("MQ connect...")
        try:
            self.connection = TornadoConnection(
                self.connection_parameters,
                self.on_connected
            )
            self.connection.add_on_close_callback(self.on_close)
        except socket.error, e:
            logging.warn("connection failed, trying again in 5 seconds")
            self.io_loop.add_timeout(time.time() + 5, self.connect)

    def on_close(self, connection):
        logging.error("Connection closed, trying reconnect in 5 seconds")
        self.io_loop.add_timeout(time.time() + 5, self.connect)

    def on_connected(self, connection):
        logging.info("Connected to AMQP server")
        connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        logging.info("AMQP channel is open")
        self.channel = channel
        self.channel.exchange_declare(
            exchange=self.exchange,
            type="fanout",
            callback=self.on_exchange_declared
        )

    def on_exchange_declared(self, frame):
        logging.info("AMQP exchange declared : " + self.exchange)

    def send_msg(self, msg, content_type="text/plain"):
        if not isinstance(msg, basestring):
            msg = json.dumps(msg)
            content_type = "application/json"
        logging.debug("MQ > %s" % str(msg))
        self.channel.basic_publish(
            exchange=self.exchange,
            body=msg,
            routing_key="",
            properties=pika.BasicProperties(
                content_type=content_type,
                delivery_mode=1,
            ))

