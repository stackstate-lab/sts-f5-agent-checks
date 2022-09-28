FROM 'stackstate/stackstate-agent-2:latest'
RUN apt update && \
    apt-get install -yq iputils-ping libkrb5-3 gcc g++

RUN /opt/stackstate-agent/embedded/bin/pip install https://github.com/stackstate-lab/stackstate-etl/releases/download/v0.2.0/stackstate-etl-py27-0.2.0.tar.gz
RUN /opt/stackstate-agent/embedded/bin/pip install https://github.com/stackstate-lab/stackstate-etl-agent-check/releases/download/v0.2.0/stackstate-etl-agent-check-py27-0.2.0.tar.gz

RUN /opt/stackstate-agent/embedded/bin/pip install 'pydash==4.9.3'

RUN echo '#!/bin/bash\n\
    if test -f "/etc/stackstate-agent/requirements.txt"; then\n\
        echo "Installing requirement"\n\
        /opt/stackstate-agent/embedded/bin/pip install -r /etc/stackstate-agent/requirements.txt\n\
        echo "Done installing dependencies"\n\
    fi\n\
    if test -f "/etc/stackstate-agent/share/install.sh"; then\n\
        echo "Running command /etc/stackstate-agent/share/install.sh"\n\
        /etc/stackstate-agent/share/install.sh\n\
        echo "Done running command"\n\
    fi\n\
    echo "agent check $1"\n\
    agent check "$1"\n\
' >> /opt/stackstate-agent/bin/run-dev-check.sh
RUN echo '#!/bin/bash\n\
    if test -f "/etc/stackstate-agent/requirements.txt"; then\n\
        echo "Installing requirement"\n\
        /opt/stackstate-agent/embedded/bin/pip install -r /etc/stackstate-agent/requirements.txt\n\
        echo "Done running additional installation"\n\
    fi\n\
    if test -f "/etc/stackstate-agent/share/install.sh"; then\n\
        echo "Running command /etc/stackstate-agent/share/install.sh"\n\
        /etc/stackstate-agent/share/install.sh\n\
        echo "Done running additional installation"\n\
    fi\n\
    echo "agent run"\n\
    agent run\n\
' >> /opt/stackstate-agent/bin/run-agent.sh
RUN chmod +x /opt/stackstate-agent/bin/run-agent.sh /opt/stackstate-agent/bin/run-dev-check.sh
