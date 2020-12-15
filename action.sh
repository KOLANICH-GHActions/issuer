#!/usr/bin/env bash

set -e;
NEED_PYTEST=$1;

THIS_SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`; # /home/runner/work/_actions/KOLANICH-GHActions/typical-python-workflow/master
echo "This script is $THIS_SCRIPT_DIR";
THIS_SCRIPT_DIR=`realpath "${THIS_SCRIPT_DIR}"`;
echo "This script is $THIS_SCRIPT_DIR";

bash $THIS_SCRIPT_DIR/setup.sh;

python3 -m IssuerGHAction
