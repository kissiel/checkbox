# This file is part of Checkbox.
#
# Copyright 2012, 2013 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.

#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`plainbox.impl.box` -- command line interface
==================================================

.. warning::

    THIS MODULE DOES NOT HAVE STABLE PUBLIC API
"""

import logging
import os

from plainbox import __version__ as plainbox_version
from plainbox.i18n import gettext as _
from plainbox.impl.applogic import PlainBoxConfig
from plainbox.impl.commands import PlainBoxToolBase
from plainbox.impl.commands.check_config import CheckConfigCommand
from plainbox.impl.commands.dev import DevCommand
from plainbox.impl.commands.run import RunCommand
from plainbox.impl.commands.selftest import PlainboxSelfTestCommand
from plainbox.impl.commands.session import SessionCommand
from plainbox.impl.commands.startprovider import StartProviderCommand
from plainbox.impl.logging import setup_logging


logger = logging.getLogger("plainbox.box")


class PlainBoxTool(PlainBoxToolBase):
    """
    Command line interface to PlainBox
    """

    @classmethod
    def get_exec_name(cls):
        """
        Get the name of this executable
        """
        return "plainbox"

    @classmethod
    def get_exec_version(cls):
        """
        Get the version reported by this executable
        """
        return cls.format_version_tuple(plainbox_version)

    def create_parser_object(self):
        parser = super().create_parser_object()
        parser.prog = "plainbox"
        parser.usage = _("plainbox [--help] [--version] | [options] <command>"
                         " ...")
        return parser

    def add_subcommands(self, subparsers):
        """
        Add top-level subcommands to the argument parser.

        This can be overridden by subclasses to use a different set of
        top-level subcommands.
        """
        # TODO: switch to plainbox plugins
        RunCommand(self._provider_list, self._config).register_parser(
            subparsers)
        SessionCommand().register_parser(subparsers)
        PlainboxSelfTestCommand().register_parser(subparsers)
        CheckConfigCommand(self._config).register_parser(subparsers)
        DevCommand(self._provider_list, self._config).register_parser(
            subparsers)
        StartProviderCommand().register_parser(subparsers)

    @classmethod
    def get_config_cls(cls):
        """
        Get the Config class that is used by this implementation.

        This can be overridden by subclasses to use a different config
        class that is suitable for the particular application.
        """
        return PlainBoxConfig

    def get_gettext_domain(self):
        return "plainbox"

    def get_locale_dir(self):
        return os.getenv("PLAINBOX_LOCALE_DIR", None)


def main(argv=None):
    raise SystemExit(PlainBoxTool().main(argv))


def get_parser_for_sphinx():
    return PlainBoxTool().construct_parser()


# Setup logging before anything else starts working.
# If we do it in main() or some other place then unit tests will see
# "leaked" log files which are really closed when the runtime shuts
# down but not when the tests are finishing
setup_logging()
