# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from tornado import web
from .cors import CORSRequestHandler
from .graphql import GraphQLHandler
from .schema import Schema


class ExampleAPIHandler(CORSRequestHandler, GraphQLHandler):

    @property
    def schema(self):
        return Schema


class ExampleWebAPIApplication(web.Application):

    def __init__(self, settings):
        handlers = [
            (r'/graphql', ExampleAPIHandler)
        ]
        super(ExampleWebAPIApplication, self).__init__(handlers, **settings)
