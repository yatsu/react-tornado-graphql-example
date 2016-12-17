# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from zmq.eventloop import ioloop

ioloop.install()

# tornado must be imported after `ioloop.install()`
import tornado.web  # noqa
from tornado.escape import json_encode  # noqa
from tornado_cors import CorsMixin  # noqa
from .graphql import GraphQLHandler  # noqa
from .schema import Schema  # noqa


class APIHandler(CorsMixin, GraphQLHandler):

    CORS_ORIGIN = '*'
    CORS_HEADERS = 'Content-Type'
    CORS_METHODS = 'POST'
    CORS_CREDENTIALS = True

    @property
    def schema(self):
        return Schema


def launch_server(port=None, debug=False):
    app = tornado.web.Application([
        (r'/graphql', APIHandler),
    ], debug=debug)
    app.listen(port)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print('\nExit')
