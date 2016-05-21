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

    def _find_jars(self, root):
        ret = []
        for jar in glob.glob(os.path.join(root, '*.jar')):
            ret.append(os.path.join(root, os.path.basename(jar)))
        return ret

    def build(self):
        super().build()
        self.run(['ant'])

        # The setpriority syscall is needed, but currently unavailable:
        # https://bugs.launchpad.net/snappy/+bug/1577520
        opts_path = os.path.join(self.builddir, 'conf', 'jvm.options')
        for opt in ('-XX:+UseThreadPriorities', '-XX:ThreadPriorityPolicy='):
            self.run(['sed', '-i', 's,^\\({}.*\\),#\\1,'.format(opt), opts_path])

    def clean_build(self):
        super().clean_build()
        if os.path.exists(os.path.join(self.partdir, 'build.xml')):
            self.run(['ant', 'clean'])

    def env(self, root):
        # Create a cassandra.in.sh equivalent

        env = super().env(root)
        home = os.path.join(root, 'usr', 'share', 'cassandra')
        env.extend(['CASSANDRA_HOME={}'.format(home)])

        conf = os.path.join(root, 'etc', 'cassandra')
        env.extend(['CASSANDRA_CONF={}'.format(conf)])

        core_jars = self._find_jars(home)
        lib_jars = self._find_jars(os.path.join(home, 'lib'))
        env.extend(
            ['CLASSPATH={}'.format(':'.join([conf] + core_jars + lib_jars))])

        env.extend(['JAVA_AGENT="-javaagent:$CASSANDRA_HOME/lib/jamm-0.3.0.jar"'])


        # We can't use 'free' without involving snap interfaces.
        env.extend(['MAX_HEAP_SIZE=500M'])
        env.extend(['HEAP_NEWSIZE=200M'])

        # We can't use 'ldconfig' without involving snap interfaces.
        env.extend(['CASSANDRA_LIBJEMALLOC=-'])

        # sstables, etc
        env.extend(['cassandra_storagedir="$SNAP_USER_DATA"'])
        env.extend(['JAVA_OPTS="-Dcassandra.logdir=$SNAP_DATA/logs"'])
        return env
