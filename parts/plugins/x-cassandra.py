# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2016 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A plugin to build Cassandra.

This plugin runs ant, then injects Cassandra's expected environment
variables.
"""


import glob
import logging
import os
import shutil

import snapcraft
import snapcraft.common
import snapcraft.plugins.jdk


logger = logging.getLogger(__name__)


class CassandraPlugin(snapcraft.plugins.jdk.JdkPlugin):

    def __init__(self, name, options, project):
        super().__init__(name, options, project)
        self.build_packages.append('ant')

    def build(self):
        super().build()
        # Put the built jars in install/
        self.run(['ant', 'artifacts', '-Ddist.dir=%s' % self.installdir])

        # The setpriority syscall is needed, but currently unavailable:
        # https://bugs.launchpad.net/snappy/+bug/1577520
        opts_path = os.path.join(self.installdir, 'conf', 'jvm.options')
        for opt in ('-XX:+UseThreadPriorities', '-XX:ThreadPriorityPolicy='):
            self.run(['sed', '-i', 's,^\\({}.*\\),#\\1,'.format(opt), opts_path])

    def clean_build(self):
        super().clean_build()
        if os.path.exists(os.path.join(self.builddir, 'build.xml')):
            self.run(['ant', 'clean'])
