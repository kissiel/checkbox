# This file is part of Checkbox.
#
# Copyright 2012-2014 Canonical Ltd.
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
:mod:`checkbox_ng.tools` -- top-level command line tools
========================================================
"""

import logging
import os

from plainbox.impl.clitools import SingleCommandToolMixIn
from plainbox.impl.clitools import ToolBase
from plainbox.impl.providers.v1 import all_providers
from plainbox.impl.commands.selftest import SelfTestCommand

from checkbox_ng import __version__ as version
from checkbox_ng.config import CheckBoxConfig
from checkbox_ng.tests import load_unit_tests


logger = logging.getLogger("checkbox.ng.tools")


class CheckboxToolBase(ToolBase):
    """
    Base class for all checkbox-ng tools.

    This class contains some shared code like configuration, providers, i18n
    and version handling.
    """

    def __init__(self):
        """
        Initialize all the variables, real stuff happens in main()
        """
        super().__init__()
        all_providers.load()
        self._config = self.get_config_cls().get()
        self._provider_list = all_providers.get_all_plugin_objects()

    @property
    def config(self):
        """
        A Config instance
        """
        return self._config

    @property
    def provider_list(self):
        """
        A list of available providers
        """
        return self._provider_list

    @classmethod
    def get_exec_version(cls):
        """
        Get the version of the checkbox-ng package
        """
        return cls.format_version_tuple(version)

    @classmethod
    def get_config_cls(cls):
        """
        Get particular sub-class of the Config class to use
        """
        return CheckBoxConfig

    def get_gettext_domain(self):
        """
        Get the 'checkbox-ng' gettext domain
        """
        return "checkbox-ng"

    def get_locale_dir(self):
        """
        Get an optional development locale directory specific to checkbox-ng
        """
        return os.getenv("CHECKBOX_NG_LOCALE_DIR", None)


class CheckboxTool(CheckboxToolBase):
    """
    Tool that implements the new checkbox command.

    This tool has two sub-commands:

        checkbox sru - to run stable release update testing
        checkbox check-config - to validate and display system configuration
    """

    @classmethod
    def get_exec_name(cls):
        return "checkbox"

    def add_subcommands(self, subparsers):
        from checkbox_ng.commands.launcher import LauncherCommand
        from checkbox_ng.commands.service import ServiceCommand
        from checkbox_ng.commands.sru import SRUCommand
        from checkbox_ng.commands.submit import SubmitCommand
        from plainbox.impl.commands.check_config import CheckConfigCommand
        SRUCommand(
            self.provider_list, self.config
        ).register_parser(subparsers)
        CheckConfigCommand(
            self.config
        ).register_parser(subparsers)
        ServiceCommand(
            self.provider_list, self.config
        ).register_parser(subparsers)
        SubmitCommand(
            self.config
        ).register_parser(subparsers)
        LauncherCommand(
            self.provider_list, self.config
        ).register_parser(subparsers)
        SelfTestCommand(load_unit_tests).register_parser(subparsers)


class CheckboxServiceTool(SingleCommandToolMixIn, CheckboxToolBase):
    """
    A tool class that implements checkbox-gui-service.

    This tool implements the DBus service required by the C++/QML checkbox-gui
    application. It should be moved to checkbox-gui codebase later to
    facilitate synchronized releases.
    """

    @classmethod
    def get_exec_name(cls):
        return "checkbox-gui-service"

    def get_command(self):
        from checkbox_ng.commands.service import ServiceCommand
        return ServiceCommand(self.provider_list, self.config)


class CheckboxSubmitTool(SingleCommandToolMixIn, CheckboxToolBase):
    """
    A tool class that implements checkbox-submit.

    This tool implements the submit feature to send test results to the
    Canonical certification website
    """

    @classmethod
    def get_exec_name(cls):
        return "checkbox-submit"

    def get_command(self):
        from checkbox_ng.commands.submit import SubmitCommand
        return SubmitCommand(self.config)


class CheckboxLauncherTool(SingleCommandToolMixIn, CheckboxToolBase):
    """
    A tool class that implements checkbox-launcher.

    This tool implements configurable text-mode-graphics launchers that perform
    a pre-defined testing session based on the launcher profile.
    """

    @classmethod
    def get_exec_name(cls):
        return "checkbox-launcher"

    def get_command(self):
        from checkbox_ng.commands.launcher import LauncherCommand
        return LauncherCommand(self.provider_list, self.config)
