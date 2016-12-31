# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import json
import logging
from tornado import web
import os
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from .cors import CORSRequestHandler
from .graphql import GraphQLHandler
from .schema import Schema

logger = logging.getLogger('tornado')

server_index = 0


class ExampleAPIHandler(CORSRequestHandler, GraphQLHandler):

    @property
    def schema(self):
        return Schema


class CommandHandler(CORSRequestHandler, web.RequestHandler):

    def initialize(self, job_servers):
        self.job_servers = job_servers

    @web.asynchronous
    def post(self):
        global server_index
        self.set_header('Content-Type', 'application/json')

        job_server = self.job_servers[server_index]
        server_index = (server_index + 1) % len(self.job_servers)

        context = zmq.Context.instance()
        sock = context.socket(zmq.DEALER)
        sock.linger = 1000
        sock.identity = bytes(str(os.getpid()), 'ascii')
        ip = job_server['ip']
        if ip == '*':
            ip = 'localhost'
        url = 'tcp://{0}:{1}'.format(ip, job_server['zmq_port'])
        logger.info('connect %s', url)
        sock.connect(url)

        command = json.dumps({'command': self.get_argument('command')})
        logger.info('command: %s', command)
        sock.send(bytes(command, 'ascii'))

        stream = ZMQStream(sock)
        stream.on_recv(self.response_handler(sock))

    def response_handler(self, stream):
        def handler(msg):
            response = msg[0]
            logger.info('response: %s', response)
            self.write(response)
            stream.close()
            self.finish()

        return handler


class ExampleWebAPIApplication(web.Application):

    def __init__(self, settings, job_servers):
        logger.info('job_servers: %s', [s['pid'] for s in job_servers])

        handlers = [
            (r'/graphql', ExampleAPIHandler),
            (r'/command', CommandHandler, dict(job_servers=job_servers))
        ]

        super(ExampleWebAPIApplication, self).__init__(handlers, **settings)

        self.job_servers = job_servers
