# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from glob import glob
import json
import logging
import os
import re
import subprocess
import sys
from traitlets import Bool, Dict, Integer, Unicode
from traitlets.config.application import Application, catch_config_error
from zmq.eventloop import ioloop

ioloop.install()

# tornado must be imported after `ioloop.install()`
from tornado.log import LogFormatter, app_log, access_log, gen_log  # noqa
from tornado.httpserver import HTTPServer  # noqa
from .version import __version__  # noqa
from .web_app import ExampleWebAPIApplication  # noqa
from .jobserverapp import JobServerApp  # noqa


class TornadoGraphqlExampleApp(Application):

    name = 'tornado-graphql-example'
    version = __version__
    description = 'An example GraphQL API Server implemented with Tornado'

    aliases = {
        'log-level': 'TornadoGraphqlExampleApp.log_level',
        'ip': 'TornadoGraphqlExampleApp.ip',
        'port': 'TornadoGraphqlExampleApp.port',
        'allow-origin': 'TornadoGraphqlExampleApp.allow_origin',
        'allow-origin-pat': 'TornadoGraphqlExampleApp.allow_origin_pat'
    }

    flags = {
        'debug': (
            {'Application': {'log_level': logging.DEBUG}},
            'set log level to logging.DEBUG (maximize logging output)'
        ),
        'disallow-credentials': (
            {'TornadoGraphqlExampleApp': {'allow_credentials': False}},
            'set Access-Control-Allow-Credentials'
        )
    }

    subcommands = {
        'jobserverapp': (JobServerApp, JobServerApp.description)
    }

    _log_formatter_cls = LogFormatter

    def _log_level_default(self):
        return logging.INFO

    def _log_datefmt_default(self):
        return "%H:%M:%S"

    def _log_format_default(self):
        return (u'%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d '
                u'%(name)s]%(end_color)s %(message)s')

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
        help='Set the Access-Control-Allow-Credentials: true header'
    )

    ip = Unicode(
        '', config=True,
        help='The IP address the server will listen on.'
    )

    def _ip_changed(self, name, old, new):
        if new == u'*':
            self.ip = u''

    port = Integer(
        4000, config=True,
        help='The port the server will listen on.'
    )

    tornado_settings = Dict(
        config=True,
        help='tornado.web.Application settings.'
    )

    subcommand = Unicode()

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
        self.tornado_settings['debug'] = self.log_level == logging.DEBUG

        self.web_app = ExampleWebAPIApplication(self.tornado_settings, self.job_servers)
        self.http_server = HTTPServer(self.web_app)
        self.http_server.listen(self.port, self.ip)

    @catch_config_error
    def initialize(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        if argv:
            if argv[0] in self.subcommands.keys():
                self.subcommand = self.name + '-' + argv[0]
                self.argv = argv
                return

        super(TornadoGraphqlExampleApp, self).initialize(argv)

        self.init_logging()
        self.init_webapp()

    def start(self):
        super(TornadoGraphqlExampleApp, self).start()

        if self.subcommand:
            try:
                subprocess.call([self.subcommand] + self.argv[1:])
            except KeyboardInterrupt:
                self.log.info('%s interrupted...', self.subcommand)
            finally:
                return

        self.io_loop = ioloop.IOLoop.current()
        try:
            self.io_loop.start()
        except KeyboardInterrupt:
            self.log.info('TornadoGraphqlExampleApp interrupted...')

    def stop(self):
        def _stop():
            self.http_server.stop()
            self.io_loop.stop()
        self.io_loop.add_callback(_stop)

    @property
    def job_servers(self):
        env = os.environ
        xdg = env.get('XDG_RUNTIME_DIR', os.path.join(env.get('HOME'), '.config'))
        appdir = os.path.join(xdg, 'tornado-graphql-example')

        def server_info(file_path):
            app_log.debug('read server_info: %s', file_path)
            with open(file_path, 'r') as f:
                return json.load(f)

        return [server_info(f) for f in glob('{0}/jobserver-*'.format(appdir))]


main = launch_new_instance = TornadoGraphqlExampleApp.launch_instance
