# Cassandra snap

This is a confined snap of Apache Cassandra. To build it, run `snapcraft` in this directory on Ubuntu 16.04 or later.

To run, first sideload the snap with `sudo snap install cassandra_*.snap`. It will not successfully start unless you allow it to see mountpoints: `snap connect cassandra:mount-observe ubuntu-core:mount-observe`.

You can check on the status of the service with `systemctl status snap.cassandra.cassandra.service`. Custom settings are not yet supported.
