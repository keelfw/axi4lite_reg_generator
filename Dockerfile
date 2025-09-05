FROM ghdl/ghdl:ubuntu22-mcode

WORKDIR /reg

ENV DEBIAN_FRONTEND=noninteractive \
    PIPX_HOME="/usr/local/pipx" \
    PIPX_BIN_DIR="/usr/local/bin" \
    PATH="$PIPX_HOME/bin:$PIPX_HOME/bin:$PATH"

# Install packages
RUN apt-get -y update && \
    apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    python-is-python3 \
    iverilog

RUN pip install --no-cache-dir pipx && \
    pipx install uv

COPY ./ /reg/

RUN uv sync --extra dev

CMD ["sleep", "infinity"]

# To run in interactive mode:
# $ docker build -t reg_test -f Dockerfile .
# $ docker run -it --entrypoint=/bin/bash -v .:/reg reg_test
