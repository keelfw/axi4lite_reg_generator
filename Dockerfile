FROM ghdl/ghdl:ubuntu22-mcode

WORKDIR /reg

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install packages
RUN apt-get -y update && \
    apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    python-is-python3 \
    tcl-dev \
    iverilog && \
    pip install poetry

COPY ./ /reg/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction \
    && rm -rf /root/.cache/pypoetry

CMD ["sleep", "infinity"]

# To run in interactive mode:
# $ docker build -t reg_test -f Dockerfile .
# $ docker run -it --entrypoint=/bin/bash -v .:/reg reg_test
