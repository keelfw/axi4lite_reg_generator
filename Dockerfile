FROM ghdl/ghdl:ubuntu22-mcode

WORKDIR /workspaces

ENV DEBIAN_FRONTEND=noninteractive \
    PIPX_HOME="/usr/local/pipx" \
    PIPX_BIN_DIR="/usr/local/bin" \
    PATH="$PIPX_HOME/bin:$PIPX_HOME/bin:$PATH" \
    POETRY_NO_INTERACTION=1

# Install packages
RUN apt-get -y update && \
    apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    python-is-python3 \
    git \
    iverilog

RUN pip install --no-cache-dir pipx && \
    pipx install poetry

COPY ./ /workspaces/

RUN poetry install --with dev --no-interaction

CMD ["sleep", "infinity"]

# To run in interactive mode:
# $ docker build -t reg_test -f Dockerfile .
# $ docker run -it --entrypoint=/bin/bash -v .:/reg reg_test
