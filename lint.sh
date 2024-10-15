#!/bin/bash

####################
#Linting for Python#
####################

FIND_DEPTH=2
FIND_FILTER="*.py"
VENV_PIP="venv/lib/python3.10/site-packages"
TARGET="kvm"

function lint_flake8(){
    find "${TARGET}" -maxdepth "${FIND_DEPTH}" -type f -name "${FIND_FILTER}" \
     | xargs flake8
}

function lint_pylint(){
    find "${TARGET}" -maxdepth "${FIND_DEPTH}" -type f -name "${FIND_FILTER}" \
     | xargs pylint --init-hook \
     "import sys; sys.path.append('./${TARGET}'); sys.path.append('./${VENV_PIP}')"
}

isort --check "${TARGET}"
black --check "${TARGET}" --config .black.toml
lint_flake8
lint_pylint
pyright .