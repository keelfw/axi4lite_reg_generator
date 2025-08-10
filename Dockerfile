FROM ghdl/ghdl:ubuntu22-mcode

WORKDIR /reg

ENV DEBIAN_FRONTEND=noninteractive \
    PIPX_HOME="/usr/local/pipx" \
    PIPX_BIN_DIR="/usr/local/bin" \
    PATH="$PIPX_HOME/bin:$POETRY_HOME/bin:$PATH" \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1

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
    pipx install poetry

COPY ./ /reg/

RUN poetry install --no-interaction

CMD ["sleep", "infinity"]

# To run in interactive mode:
# $ docker build -t reg_test -f Dockerfile .
# $ docker run -it --entrypoint=/bin/bash -v .:/reg reg_test
