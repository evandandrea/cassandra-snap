# Cassandra snap

[![Build Status](https://travis-ci.org/evandandrea/cassandra-snap.svg?branch=master)](https://travis-ci.org/evandandrea/cassandra-snap)

This is a confined snap of Apache Cassandra. To build it, run `snapcraft` in this directory on Ubuntu 16.04 or later.

To run, sideload the snap and allow it access to mountpoints: `sudo snap install cassandra_*.snap && snap connect cassandra:mount-observe ubuntu-core:mount-observe`.

You can check on the status of the service with `systemctl status snap.cassandra.cassandra.service`. You can set a custom cassandra.yaml with `cat cassandra.yaml | sudo /snap/bin/cassandra.config-set cassandra.yaml`.
