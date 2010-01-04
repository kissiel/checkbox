#
# This file is part of Checkbox.
#
# Copyright 2008 Canonical Ltd.
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.
#
from checkbox.lib.cache import cache

from checkbox.frontend import frontend
from checkbox.job import Job, PASS
from checkbox.properties import Int, String
from checkbox.registry import Registry


class CommandRegistry(Registry):
    """Base registry for running commands.

    The default behavior is to return the output of the command.

    Subclasses should define a command parameter.
    """

    command = String()

    timeout = Int(required=False)

    def __init__(self, command=None):
        super(CommandRegistry, self).__init__()
        if command is not None:
            self.command = command

    @frontend("get_registry")
    def __str__(self):
        job = Job(self.command, timeout=self.timeout)
        (status, data, duration) = job.execute()
        # Return empty string if the job failed
        if status != PASS:
            return ""

        return data

    @cache
    def items(self):
        # Force running the command
        item = str(self)
        return []
