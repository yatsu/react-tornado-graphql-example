# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from functools import wraps
import graphql
from graphql.error import GraphQLError
from graphql.error import format_error as format_graphql_error
from graphql.execution import ExecutionResult
import logging
import sys
from tornado import gen, web
from tornado.escape import json_decode, json_encode, to_unicode
from tornado.log import app_log
import traceback


def error_status(exception):
    if isinstance(exception, web.HTTPError):
        return exception.status_code
    elif isinstance(exception, (ExecutionError, GraphQLError)):
        return 400
    else:
        return 500


def error_format(exception):
    if isinstance(exception, ExecutionError):
        return [{'message': e} for e in exception.errors]
    elif isinstance(exception, GraphQLError):
        return [format_graphql_error(exception)]
    elif isinstance(exception, web.HTTPError):
        return [{'message': exception.log_message,
                 'reason': exception.reason}]
    else:
        return [{'message': 'Unknown server error'}]


def error_response(func):
    @wraps(func)
    @gen.coroutine
    def wrapper(self, *args, **kwargs):
        try:
            result = yield gen.maybe_future(func(self, *args, **kwargs))
        except Exception as ex:
            self.set_status(error_status(ex))
            self.set_header('Content-Type', 'application/json')
            if not isinstance(ex, (web.HTTPError, ExecutionError, GraphQLError)):
                tb = ''.join(traceback.format_exception(*sys.exc_info()))
                app_log.error('Error: {0} {1}'.format(ex, tb))
            self.finish(json_encode({'errors': error_format(ex)}))
        else:
            raise gen.Return(result)

    return wrapper


class ExecutionError(Exception):
    def __init__(self, status_code=400, errors=None):
        self.status_code = status_code
        if errors is None:
            self.errors = []
        else:
            self.errors = errors


class GraphQLRequest(object):
    def __init__(self, query=None, variables=None, operation_name=None, raw=None):
        self.query = query
        self.variables = variables
        self.operation_name = operation_name
        self.raw = raw

    def __repr__(self):
        props = ', '.join('{0}={1}'.format(k, v) for k, v in self.__dict__.items())
        return '<%s {%s}>' % (self.__class__.__name__, props)


class GraphQLHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        yield self.handle_graqhql()

    @error_response
    @gen.coroutine
    def handle_graqhql(self):
        self.set_header('Content-Type', 'application/json')

        result = self.execute_graphql()
        if result and result.invalid:
            app_log.warn('GraphQL Error {0}'.format(result.errors))
            raise ExecutionError(errors=result.errors)

        response = {'data': result.data}
        if result.errors:
            response['errors'] = result.errors
        self.write(json_encode(response))

    def execute_graphql(self):
        graphql_req = self.graphql_request
        app_log.info('graphql_req: {0}'.format(graphql_req))

        try:
            source = graphql.Source(graphql_req.query, name='GraphQL request')
            ast = graphql.parse(source)
            verrors = graphql.validate(self.schema, ast)
            if verrors:
                return ExecutionResult(errors=verrors, invalid=True)
            return graphql.execute(self.schema, ast, root_value=self.root_value,
                                   variable_values=graphql_req.variables,
                                   operation_name=graphql_req.operation_name,
                                   context_value=self.context)

        except Exception as ex:
            tb = ''.join(traceback.format_exception(*sys.exc_info()))
            app_log.error('Error: {0} {1}'.format(ex, tb))
            return ExecutionResult(errors=[ex], invalid=True)

    @property
    def graphql_request(self):
        content_type = self.content_type
        if content_type == 'application/graphql':
            req = {'query': to_unicode(self.request.body).strip()}

        elif content_type == 'application/json':
            try:
                req = json_decode(self.request.body)
                assert isinstance(req, dict)
            except:
                app_log.warn('Invalid JSON:\n{0}'.format(self.request.body))
                raise web.HTTPError(400, 'Invalid JSON:\n{0}'.format(self.request.body))

        elif content_type in ('application/x-www-form-urlencoded',
                              'multipart/form-data'):
            raise NotImplementedError('form data is not supported yet')

        else:
            req = {}

        try:
            return GraphQLRequest(
                **{'operation_name' if k == 'operationName' else k: v
                   for k, v in req.items()}
            )
        except:
            app_log.warn('Invalid JSON:\n{0}'.format(req))
            raise web.HTTPError(400, 'Invalid JSON:\n{0}'.format(req))

    @property
    def content_type(self):
        return self.request.headers.get('Content-Type', 'text/plain').split(';')[0]

    @property
    def schema(self):
        raise NotImplementedError('schema must be provided')

    @property
    def root_value(self):
        return None

    @property
    def context(self):
        return None
