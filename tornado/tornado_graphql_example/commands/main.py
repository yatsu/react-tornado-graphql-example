# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import sys
from tornado_graphql_example.version import __version__
from cliff.app import App
from cliff.commandmanager import CommandManager


class TornadoGraphqlExampleApp(App):

    def __init__(self):
        super(TornadoGraphqlExampleApp, self).__init__(
            description='tornado_graphql_example',
            version=__version__,
            command_manager=CommandManager(
                'tornado_graphql_example.commands',
                convert_underscores=False
            )
        )


def main(argv=sys.argv[1:]):
    return TornadoGraphqlExampleApp().run(argv)
