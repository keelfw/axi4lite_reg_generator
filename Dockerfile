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

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y \
    rlwrap \
    tclsh \
    tcllib \
    git \
    vim

COPY ./ /reg/

# RUN mkdir -p /osvvm/libs && \
#     git clone --recursive https://github.com/osvvm/OsvvmLibraries /osvvm/OsvvmLibraries && \
#     tclsh compile_osvvm.tcl

# RUN echo -e 'namespace eval ::osvvm {\nvariable VhdlLibraryParentDirectory "/osvvm/libs"\n}' > \
#     /osvvm/OsvvmLibraries/Scripts/OsvvmSettingsLocal.tcl

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction \
    && rm -rf /root/.cache/pypoetry

CMD ["poetry", "run", "pytest"]

# docker build -t ghdl-test .