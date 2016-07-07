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


import logging
import os
from urllib.parse import urlparse

import snapcraft
import snapcraft.common
import snapcraft.plugins.jdk


logger = logging.getLogger(__name__)


def _get_no_proxy_string():
    no_proxy = [k.strip() for k in
                os.environ.get('no_proxy', 'localhost').split(',')]
    return '|'.join(no_proxy)


class CassandraPlugin(snapcraft.plugins.jdk.JdkPlugin):

    def __init__(self, name, options, project):
        super().__init__(name, options, project)
        self.build_packages.append('ant')


    def _use_proxy(self):
        keys = ('SNAPCRAFT_LOCAL_SOURCES', 'http_proxy')
        return all([k in os.environ for k in keys])


    def pull(self):
        super().pull()
        # Isolate fetching deps from the Internet to the pull() step, so that
        # this builds on Launchpad.
        env = os.environ.copy()
        if self._use_proxy():
            http = urlparse(os.environ['http_proxy'])
            https = urlparse(os.environ['https_proxy'])
            no_proxy = _get_no_proxy_string()

            proxy = ('-Dhttp.proxyHost={http_host}'
                     ' -Dhttp.proxyPort={http_port}'
                     ' -Dhttp.nonProxyHosts={no_proxy}'
                     ' -Dhttps.proxyHost={https_host}'
                     ' -Dhttps.proxyPort={https_port}'
                     ' -Dhttps.nonProxyHosts={no_proxy}')
            env['ANT_OPTS'] = proxy.format(http_host=http.hostname,
                                           http_port=http.port,
                                           https_host=https.hostname,
                                           https_port=https.port,
                                           no_proxy=no_proxy)
             
        snapcraft.BasePlugin.build(self)
        self.run(['ant', 'maven-ant-tasks-download'], env=env)


    def build(self):
        # Put the built jars in install/
        command = ['ant', 'artifacts', '-Ddist.dir=%s' % self.installdir]
        # snapcraft cleanbuild will fail unless you tell javadoc to use UTF8.
        self.run(command, env={'JAVA_TOOL_OPTIONS': '-Dfile.encoding=UTF8'})

        # The setpriority syscall is needed, but currently unavailable:
        # https://bugs.launchpad.net/snappy/+bug/1577520
        opts_path = os.path.join(self.installdir, 'conf', 'jvm.options')
        for opt in ('-XX:+UseThreadPriorities', '-XX:ThreadPriorityPolicy='):
            self.run(['sed', '-i', 's,^\\({}.*\\),#\\1,'.format(opt), opts_path])

    def clean_build(self):
        super().clean_build()
        if os.path.exists(os.path.join(self.builddir, 'build.xml')):
            self.run(['ant', 'clean'])
