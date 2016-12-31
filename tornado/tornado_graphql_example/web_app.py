# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
from tornado import web
from .cors import CORSRequestHandler
from .graphql import GraphQLHandler
from .schema import Schema

logger = logging.getLogger('tornado')


class ExampleAPIHandler(CORSRequestHandler, GraphQLHandler):

    @property
    def schema(self):
        return Schema


class CommandHandler(CORSRequestHandler, web.RequestHandler):

    def post(self):
        self.set_header('Content-Type', 'application/json')
        self.write({'result': 'ok'})


class ExampleWebAPIApplication(web.Application):

    def __init__(self, settings, job_servers):
        logger.info('job_servers: %s', [s['pid'] for s in job_servers])

        handlers = [
            (r'/graphql', ExampleAPIHandler),
            (r'/command', CommandHandler)
        ]

        super(ExampleWebAPIApplication, self).__init__(handlers, **settings)

        self.job_servers = job_servers
