#!/bin/bash

echo "Installing stackstate-etl package"
/opt/stackstate-agent/embedded/bin/pip install /etc/stackstate-agent/share/pkgs/stackstate-etl-py27-0.1.0.tar.gz
/opt/stackstate-agent/embedded/bin/pip install /etc/stackstate-agent/share/pkgs/stackstate-etl-agent-check-py27-0.1.0.tar.gz