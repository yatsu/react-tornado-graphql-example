# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from cliff.command import Command
from ..server import launch_server


class RunCommand(Command):

    def get_parser(self, prog_name):
        parser = super(RunCommand, self).get_parser(prog_name)
        parser.add_argument('-p', '--port', type=int, default=4000,
                            help='TCP port (default: %(default)s)')
        parser.add_argument('-d', '--debug', action='store_true',
                            help='enable debug')

        return parser

    def take_action(self, parsed_args):
        launch_server(**self._construct_options(parsed_args))

    def _construct_options(self, parsed_args):
        return {
            'port': parsed_args.port,
            'debug': parsed_args.debug
        }
