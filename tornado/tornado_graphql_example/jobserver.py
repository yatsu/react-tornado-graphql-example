# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import errno
import json
import logging
import os
from subprocess import check_output
from time import sleep
from tornado.log import LogFormatter
from traitlets import Integer, Unicode
from traitlets.config.application import Application, catch_config_error
import zmq
from .version import __version__


class JobServer(Application):

    name = 'tornado-graphql-example-jobserver'
    version = __version__
    description = 'A job server for TornadoGraphqlExample'

    aliases = {
        'log-level': 'Application.log_level',
        'ip': 'JobServer.ip',
        'port': 'JobServer.port',
        'sleep': 'JobServer.sleep'
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

    sleep = Integer(
        0, config=True,
        help='Suspend executing each job for the specified numbrer of seconds'
    )

    pid = Integer()

    zmq_port = Integer()

    def __repr__(self):
        return '<%s {pid=%d ip=%s port=%d sleep=%d}>' % (
            self.__class__.__name__, self.pid, self.ip, self.zmq_port, self.sleep)

    def __call__(self):
        self.start()

    @property
    def info_file(self):
        env = os.environ
        xdg = env.get('XDG_RUNTIME_DIR', os.path.join(env.get('HOME'), '.config'))
        appdir = os.path.join(xdg, 'tornado-graphql-example')
        return os.path.join(appdir, 'jobserver-{0}'.format(self.pid))

    @property
    def server_info(self):
        return {
            'pid': self.pid,
            'ip': self.ip,
            'port': self.port,
            'zmq_port': self.zmq_port,
            'sleep': self.sleep
        }

    def write_server_info_file(self):
        dirname = os.path.dirname(self.info_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(self.info_file, 'w') as f:
            json.dump(self.server_info, f, indent=2, sort_keys=True)

    def remove_server_info_file(self):
        try:
            os.unlink(self.info_file)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    @catch_config_error
    def initialize(self, argv=None):
        super(JobServer, self).initialize(argv)

        if self.log.level == logging.DEBUG:
            self.debug = True

    def start(self):
        self.pid = os.getpid()
        context = zmq.Context.instance()
        sock = context.socket(zmq.DEALER)
        sock.linger = 1000
        sock.identity = bytes(str(self.pid), 'ascii')
        if self.port == 0:
            self.zmq_port = sock.bind_to_random_port('tcp://{0}'.format(self.ip))
        else:
            self.zmq_port = sock.bind('tcp://{0}:{1}'.format(self.ip, self.port))
        self.log_format = (u'%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d '
                           u'%(name)s-{0}]%(end_color)s %(message)s').format(self.pid)
        self.log.info('start %s', self)

        self.write_server_info_file()

        try:
            while True:
                msg = json.loads(str(sock.recv(), 'ascii'))
                if 'command' in msg:
                    result = self.handle_command_event(**msg)
                    response = {'result': str(result, 'ascii')}
                else:
                    response = {'error': 'Invalid message: {0}'.format(msg)}
                self.log.info('response: %s', response)
                sock.send(bytes(json.dumps(response), 'ascii'))
        finally:
            self.remove_server_info_file()

    def handle_command_event(self, command, **args):
        if self.sleep > 0:
            self.log.info('sleep %d', self.sleep)
            sleep(self.sleep)
        result = check_output(command)
        return result

    def stop(self):
        def _stop():
            self.io_loop.stop()
        self.io_loop.add_callback(_stop)


main = launch_new_instance = JobServer.launch_instance
