# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
from tornado.log import LogFormatter
from traitlets import Integer, Unicode
from traitlets.config.application import Application, catch_config_error
import zmq
from zmq.eventloop import ioloop
from .version import __version__


class JobServer(Application):

    name = 'tornado-graphql-example-jobserver'
    version = __version__
    description = 'A job server for TornadoGraphqlExample'

    aliases = {
        'log-level': 'Application.log_level',
        'ip': 'JobServerApp.ip',
        'port': 'JobServerApp.port'
    }

    flags = {
        'debug': (
            {'Application': {'log_level': logging.DEBUG}},
            'set log level to logging.DEBUG (maximize logging output)'
        )
    }

    _log_formatter_cls = LogFormatter

    def _log_level_default(self):
        return logging.INFO

    def _log_datefmt_default(self):
        return "%H:%M:%S"

    def _log_format_default(self):
        return (u'%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d '
                u'%(name)s]%(end_color)s %(message)s')

    ip = Unicode(
        '*', config=True,
        help='The IP address the server will listen on.'
    )

    port = Integer(
        0, config=True,
        help='The port the server will listen on.'
    )

    pid = Integer()

    zmq_port = Integer()

    def __repr__(self):
        return '<%s {pid=%d ip=%s port=%d}>' % (
            self.__class__.__name__, self.pid, self.ip, self.zmq_port)

    def __call__(self):
        self.start()

    @catch_config_error
    def initialize(self, argv=None):
        super(JobServer, self).initialize(argv)

        if self.log.level == logging.DEBUG:
            self.debug = True

    def start(self):
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        if self.port == 0:
            self.zmq_port = socket.bind_to_random_port('tcp://{0}'.format(self.ip))
        else:
            self.zmq_port = socket.bind('tcp://{0}:{1}'.format(self.ip, self.port))
        self.pid = os.getpid()
        self.log_format = (u'%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d '
                           u'%(name)s-{0}]%(end_color)s %(message)s').format(self.pid)
        self.log.info('start %s', self)

        self.io_loop = ioloop.IOLoop.current()
        self.io_loop.start()

    def stop(self):
        def _stop():
            self.io_loop.stop()
        self.io_loop.add_callback(_stop)


main = launch_new_instance = JobServer.launch_instance
