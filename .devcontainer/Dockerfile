FROM ghdl/ghdl:ubuntu22-mcode

WORKDIR /reg

RUN apt-get -y update && \
    apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    python-is-python3 && \
    pip install poetry

COPY . /reg/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction \
    && rm -rf /root/.cache/pypoetry

CMD ["sleep", "infinity"]