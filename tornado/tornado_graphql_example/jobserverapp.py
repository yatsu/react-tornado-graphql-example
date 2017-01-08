# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
from multiprocessing import Process
from traitlets import Bool, Integer, List, Unicode
from traitlets.config.application import Application, catch_config_error
from zmq.eventloop import ioloop
from .version import __version__


ioloop.install()

# tornado must be imported after `ioloop.install()`
from tornado.log import LogFormatter  # noqa
from .jobserver import JobServer  # noqa


class JobServerApp(Application):

    name = 'tornado-graphql-example-jobserver'
    version = __version__
    description = 'A job server for TornadoGraphqlExampleApp'

    aliases = {
        'log-level': 'Application.log_level',
        'ip': 'JobServerApp.ip',
        'ports': 'JobServerApp.ports',
        'num': 'JobServerApp.num',
        'sleep': 'JobServerApp.sleep'
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

    ports = List(
        config=True,
        help='The ports the servers will listen on.'
    )

    num = Integer(
        3, config=True,
        help='The number of the servers to be launched.'
    )

    sleep = Integer(
        0, config=True,
        help='Suspend executing each job for the specified numbrer of seconds'
    )

    procs = List()

    debug = Bool(False)

    @catch_config_error
    def initialize(self, argv=None):
        super(JobServerApp, self).initialize(argv)

        if self.log.level == logging.DEBUG:
            self.debug = True

    def start(self):
        for i in range(self.num):
            self.start_jobserver(i)

        if self.debug:
            self.io_loop = ioloop.IOLoop.current()
            try:
                self.io_loop.start()
            except KeyboardInterrupt:
                print('Interrupted...')
                for i, proc in enumerate(self.procs):
                    print('terminate jobserver {0}: {1}'.format(i, proc))
                    proc.terminate()

    def start_jobserver(self, i):
        try:
            port = (self.ports or [])[i]
        except IndexError:
            port = 0
        job_server = JobServer(log_level=self.log_level, ip=self.ip, port=port,
                               sleep=self.sleep)
        job_server.log.parent = self.log
        # self.log.debug('start %s', job_server)
        proc = Process(target=job_server)
        proc.start()
        self.procs.append(proc)


main = launch_new_instance = JobServerApp.launch_instance
