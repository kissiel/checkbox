#!/usr/bin/env python3
# This file is part of Checkbox.
#
# Copyright 2013 Canonical Ltd.
# Written by:
#   Sylvain Pineau <sylvain.pineau@canonical.com>
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

from distutils.ccompiler import new_compiler
from glob import glob
import os

from DistUtilsExtra.command import build_extra
import DistUtilsExtra.auto

with open("README.rst", encoding="UTF-8") as stream:
    LONG_DESCRIPTION = stream.read()

PROVIDER_PATH = "/usr/lib/plainbox-providers-1/checkbox/"

DATA_FILES = [
    (os.path.join(PROVIDER_PATH, 'bin'), glob("provider_bin/*")),
    (os.path.join(PROVIDER_PATH, 'whitelists'), glob("provider_whitelists/*")),
    ("/usr/share/plainbox-providers-1", ["checkbox.provider"])
]
DATA_FILES.extend([
    (os.path.join(PROVIDER_PATH, root.replace('provider_data', 'data')),
        [os.path.join(root, f) for f in files])
    for root, dirs, files in os.walk('provider_data', followlinks=True)
])


class Build(build_extra.build_extra):

    def run(self):
        build_extra.build_extra.run(self)
        cc = new_compiler()
        for source in glob('provider_bin/*.c'):
            executable = os.path.splitext(source)[0]
            cc.link_executable(
                [source], executable, libraries=["rt", "pthread"],
                # Enforce security with dpkg-buildflags --get CFLAGS
                extra_preargs=[
                    "-g", "-O2", "-fstack-protector",
                    "--param=ssp-buffer-size=4", "-Wformat",
                    "-Werror=format-security"])


DistUtilsExtra.auto.setup(
    # To work as expected, the provider content lives in directories starting
    # with provider_ so that DistUtilsExtra auto features avoid putting files
    # in /usr/bin and /usr/share automatically.
    name="plainbox-provider-checkbox",
    version="0.4.dev",
    url="https://launchpad.net/checkbox/",
    author="Sylvain Pineau",
    author_email="sylvain.pineau@canonical.com",
    license="GPLv3+",
    description="CheckBox provider",
    long_description=LONG_DESCRIPTION,
    data_files=DATA_FILES,
    cmdclass={'build': Build},
    )
