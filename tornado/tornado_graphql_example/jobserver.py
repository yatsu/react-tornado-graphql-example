# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import atexit
from datetime import datetime
import errno
import json
import logging
import os
import shlex
from traitlets import Bool, Integer, Unicode
from traitlets.config.application import Application, catch_config_error
import zmq
from zmq.eventloop import ioloop, zmqstream

ioloop.install()

# tornado must be imported after `ioloop.install()`
from tornado import gen  # noqa
from tornado.iostream import StreamClosedError  # noqa
from tornado.log import LogFormatter  # noqa
from tornado.process import Subprocess  # noqa
from .version import __version__  # noqa


class JobServer(Application):

    name = 'tornado-graphql-example-jobserver'
    version = __version__
    description = 'A job server for TornadoGraphqlExample'

    aliases = {
        'log-level': 'Application.log_level',
        'ip': 'JobServer.ip',
        'port': 'JobServer.port'
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
            'zmq_port': self.zmq_port
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

    debug = Bool(False)

    @catch_config_error
    def initialize(self, argv=None):
        super(JobServer, self).initialize(argv)

        if self.log.level == logging.DEBUG:
            self.debug = True

    def start(self):
        self.pid = os.getpid()
        context = zmq.Context.instance()
        zmq_sock = context.socket(zmq.DEALER)
        zmq_sock.linger = 1000
        zmq_sock.identity = bytes(str(self.pid), 'ascii')
        if self.port == 0:
            self.zmq_port = zmq_sock.bind_to_random_port('tcp://{0}'.format(self.ip))
        else:
            self.zmq_port = zmq_sock.bind('tcp://{0}:{1}'.format(self.ip, self.port))

        self.zmq_stream = zmqstream.ZMQStream(zmq_sock)
        self.zmq_stream.on_recv(self.request_handler)

        self.log_format = (u'%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d '
                           u'%(name)s-{0}]%(end_color)s %(message)s').format(self.pid)
        self.log.info('start %s', self)

        self.write_server_info_file()

        atexit.register(self.remove_server_info_file)

        self.io_loop = ioloop.IOLoop.current()
        try:
            self.io_loop.start()
        except KeyboardInterrupt:
            self.log.info('JobServer interrupted...')
        finally:
            self.remove_server_info_file()

    @gen.coroutine
    def request_handler(self, msg):
        ident, request = msg
        req_data = json.loads(request.decode('utf-8'))
        self.log.info('request: %s', req_data)

        if 'command' not in req_data:
            raise ValueError('command must be specified in a request')
        command = req_data['command']
        if command == 'countdown':
            yield self.countdown_handler(
                req_data.get('interval', 0),
                req_data.get('count', 5)
            )
        else:
            raise ValueError("Unknown command '{0}'".format(command))

    @gen.coroutine
    def countdown_handler(self, interval, count):
        command = '{0}/countdown -i {1} {2}'.format(os.getcwd(), interval, count)
        proc = Subprocess(shlex.split(command), stdout=Subprocess.STREAM)
        try:
            while True:
                line_bytes = yield proc.stdout.read_until(b'\n')
                line = line_bytes.decode('utf-8')[:-1]
                self.log.info('command read: %s', line)
                timestamp = datetime.now().timestamp()
                self.zmq_stream.send_multipart([b'0', json.dumps({
                    'stdout': line,
                    'finished': False,
                    'timestamp': timestamp
                }).encode('utf-8')])
        except StreamClosedError:
            self.log.info('command closed')
            timestamp = datetime.now().timestamp()
            self.zm_stream.send_multipart([b'0', json.dumps({
                'stdout': None,
                'finished': False,
                'timestamp': timestamp
            }).encode('utf-8')])

    def stop(self):
        def _stop():
            self.io_loop.stop()
        self.io_loop.add_callback(_stop)


main = launch_new_instance = JobServer.launch_instance
