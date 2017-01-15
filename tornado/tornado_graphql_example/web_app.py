# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from tornado import web
from tornado.escape import json_decode, json_encode, to_unicode
from tornado.log import app_log
import os
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from .cors import CORSRequestHandler
from .graphql import GraphQLHandler, GraphQLSubscriptionHandler
from .schema import schema


class ExampleAPIHandler(CORSRequestHandler, GraphQLHandler):

    def initialize(self, opts):
        super(ExampleAPIHandler, self).initialize()

        self.opts = opts
        self._schema = schema

    @property
    def schema(self):
        return self._schema


class SubscriptionHandler(GraphQLSubscriptionHandler):

    def initialize(self, opts):
        super(SubscriptionHandler, self).initialize()

        self.opts = opts
        self._schema = schema

    @property
    def schema(self):
        return self._schema

    @property
    def sockets(self):
        return self.opts['sockets']

    @property
    def subscriptions(self):
        return self.opts['subscriptions'].get(self, {})

    @subscriptions.setter
    def subscriptions(self, subscriptions):
        self.opts['subscriptions'][self] = subscriptions

    @property
    def job_servers(self):
        return self.opts['job_servers']

    @property
    def job_server_index(self):
        return self.opts['job_server_index']

    @job_server_index.setter
    def job_server_index(self, job_server_index):
        self.opts['job_server_index'] = job_server_index

    @property
    def allow_origin(self):
        return self.opts['allow_origin']

    @property
    def allow_origin_pat(self):
        return self.opts['allow_origin_pat']

    def check_origin(self, origin):
        if self.allow_origin == '*':
            return True
        elif self.allow_origin:
            return origin == self.allow_origin
        elif self.allow_orogin_pat:
            return self.allow_origin_path.scan(origin) is not None
        else:
            return False

    def on_subscribe(self, subid, data):
        super(SubscriptionHandler, self).on_subscribe(subid, data)

        query = data.get('query')
        op_name = self._get_op_name(query)

        if op_name == 'commandExecute':
            self._execute_command('countdown')  # TODO: get command name

    def _execute_command(self, command):
        if len(self.job_servers) == 0:
            app_log.error('there is no job server')
            return

        server = self.job_servers[self.job_server_index]
        self.job_server_index = (self.job_server_index + 1) % len(self.job_servers)

        context = zmq.Context.instance()
        zmq_sock = context.socket(zmq.DEALER)
        zmq_sock.linger = 1000
        zmq_sock.identity = bytes(str(os.getpid()), 'ascii')
        ip = server['ip']
        if ip == '*':
            ip = 'localhost'
        url = 'tcp://{0}:{1}'.format(ip, server['zmq_port'])
        app_log.info('connect %s', url)
        zmq_sock.connect(url)

        command = json_encode({'command': command})
        app_log.info('command: %s', command)
        zmq_sock.send_multipart([b'0', bytes(command, 'ascii')])

        stream = ZMQStream(zmq_sock)
        stream.on_recv(self.response_handler)

    def response_handler(self, msg):
        ident, resp_bytes = msg
        resp = json_decode(to_unicode(resp_bytes))
        app_log.debug('resp: %s', resp)

        subid = self.subscriptions.get('commandExecute')
        if subid is not None:
            self.write_message(json_encode({
                'type': 'subscription_data',
                'id': subid,
                'payload': {
                    'data': resp
                }
            }))


class ExampleWebAPIApplication(web.Application):

    def __init__(self, settings, job_servers):
        app_log.info('job_servers: %s', [s['pid'] for s in job_servers])

        self.opts = dict(settings, **{
            'job_servers': job_servers,
            'job_server_index': 0,
            'sockets': [],
            'subscriptions': {}
        })

        handlers = [
            (r'/', SubscriptionHandler, dict(opts=self.opts)),
            (r'/graphql', ExampleAPIHandler, dict(opts=self.opts))
        ]

        super(ExampleWebAPIApplication, self).__init__(handlers, **settings)
