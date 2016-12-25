# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import re
from traitlets import Bool, Dict, Integer, Unicode
from traitlets.config.application import Application, catch_config_error
from zmq.eventloop import ioloop

ioloop.install()

# tornado must be imported after `ioloop.install()`
from tornado.escape import json_encode  # noqa
from tornado.log import LogFormatter, app_log, access_log, gen_log  # noqa
from tornado.httpserver import HTTPServer  # noqa
from .version import __version__  # noqa
from .web_app import ExampleWebAPIApplication  # noqa


class TornadoGraphqlExampleApp(Application):

    name = 'tornado-graphql-example'
    version = __version__
    description = 'An example GraphQL API Server implemented with Tornado'

    aliases = {
        'log-level': 'TornadoGraphqlExampleApp.log_level',
        'ip': 'TornadoGraphqlExampleApp.ip',
        'port': 'TornadoGraphqlExampleApp.port'
    }

    flags = {
        'debug': (
            {'Application': {'log_level': logging.DEBUG}},
            'set log level to logging.DEBUG (maximize logging output)'
        ),
    }

    # subcommands = {
    #     'list': (JobServerApp, JobServerApp.description)
    # }

    _log_formatter_cls = LogFormatter

    def _log_level_default(self):
        return logging.INFO

    def _log_datefmt_default(self):
        """Exclude date from default date format"""
        return "%H:%M:%S"

    def _log_format_default(self):
        """override default log format to include time"""
        return (
            u"%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d]"
            u"%(end_color)s %(message)s"
        )

    allow_origin = Unicode(
        '*', config=True,
        help="""Set the Access-Control-Allow-Origin header

        Use '*' to allow any origin to access your server.

        Takes precedence over allow_origin_pat.
        """
    )

    allow_origin_pat = Unicode(
        '', config=True,
        help="""Use a regular expression for the Access-Control-Allow-Origin header

        Requests from an origin matching the expression will get replies with:

            Access-Control-Allow-Origin: origin

        where `origin` is the origin of the request.

        Ignored if allow_origin is set.
        """
    )

    allow_credentials = Bool(
        True, config=True,
        help="Set the Access-Control-Allow-Credentials: true header"
    )

    ip = Unicode(
        'localhost', config=True,
        help="The IP address the server will listen on."
    )

    def _ip_changed(self, name, old, new):
        if new == u'*':
            self.ip = u''

    port = Integer(
        4000, config=True,
        help="The port the server will listen on."
    )

    tornado_settings = Dict(
        config=True,
        help='Supply overrides for the tornado.web.Application that the server uses.'
    )

    def init_logging(self):
        self.log.propagate = False

        for log in app_log, access_log, gen_log:
            log.name = self.log.name

        logger = logging.getLogger('tornado')
        logger.propagate = True
        logger.parent = self.log
        logger.setLevel(self.log.level)

    def init_webapp(self):
        self.tornado_settings['allow_origin'] = self.allow_origin
        if self.allow_origin_pat:
            self.tornado_settings['allow_origin_pat'] = re.compile(self.allow_origin_pat)
        self.tornado_settings['allow_credentials'] = self.allow_credentials

        self.web_app = ExampleWebAPIApplication(self.tornado_settings)
        self.http_server = HTTPServer(self.web_app)
        self.http_server.listen(self.port, self.ip)

    @catch_config_error
    def initialize(self, argv=None):
        super(TornadoGraphqlExampleApp, self).initialize(argv)
        self.init_logging()
        self.init_webapp()

    def start(self):
        super(TornadoGraphqlExampleApp, self).start()

        self.io_loop = ioloop.IOLoop.current()
        try:
            self.io_loop.start()
        except KeyboardInterrupt:
            self.log.info("Interrupted...")

    def stop(self):
        def _stop():
            self.http_server.stop()
            self.io_loop.stop()
        self.io_loop.add_callback(_stop)


main = launch_new_instance = TornadoGraphqlExampleApp.launch_instance
