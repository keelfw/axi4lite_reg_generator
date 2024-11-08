FROM ghdl/ghdl:ubuntu22-mcode

WORKDIR "/reg"

RUN apt-get -y update && \
    apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    python3-virtualenv \
    python3-poetry \
    python-is-python3

COPY ./ /reg/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction \
    && rm -rf /root/.cache/pypoetry

CMD ["poetry", "run", "pytest", "--cov=axi4lite_reg_generator", "--cov-report=xml"]

# docker build -t ghdl-test .