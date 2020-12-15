#!/usr/bin/env bash

set -e;
NEED_PYTEST=$1;

THIS_SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`; # /home/runner/work/_actions/KOLANICH-GHActions/typical-python-workflow/master
echo "This script is $THIS_SCRIPT_DIR";
THIS_SCRIPT_DIR=`realpath "${THIS_SCRIPT_DIR}"`;
echo "This script is $THIS_SCRIPT_DIR";
ACTIONS_DIR=`realpath "$THIS_SCRIPT_DIR/../../.."`;

AUTHOR_NAMESPACE=KOLANICH-GHActions;

SETUP_ACTION_REPO=$AUTHOR_NAMESPACE/setup-python;
GIT_PIP_ACTION_REPO=$AUTHOR_NAMESPACE/git-pip;
APT_ACTION_REPO=$AUTHOR_NAMESPACE/git-pip;

SETUP_ACTION_DIR=$ACTIONS_DIR/$SETUP_ACTION_REPO/master;
GIT_PIP_ACTION_DIR=$ACTIONS_DIR/$GIT_PIP_ACTION_REPO/master;
APT_ACTION_DIR=$ACTIONS_DIR/$APT_ACTION_REPO/master;

if [ -d "$SETUP_ACTION_DIR" ]; then
	:
else
	git clone --depth=1 https://github.com/$SETUP_ACTION_REPO $SETUP_ACTION_DIR;
fi;

if [ -d "$GIT_PIP_ACTION_DIR" ]; then
	:
else
	git clone --depth=1 https://github.com/$GIT_PIP_ACTION_REPO $GIT_PIP_ACTION_DIR;
fi;

if [ -d "$APT_ACTION_DIR" ]; then
	:
else
	git clone --depth=1 https://github.com/$APT_ACTION_REPO $APT_ACTION_DIR;
fi;

bash $SETUP_ACTION_DIR/action.sh 0;

bash $GIT_PIP_ACTION_DIR/action.sh $THIS_SCRIPT_DIR/pythonPackagesToInstallFromGit.txt;
bash $APT_ACTION_DIR/action.sh $THIS_SCRIPT_DIR/pythonPackagesToInstallFromGit.txt;

echo "##[group] Getting package name";
PACKAGE_NAME=`python3 $THIS_SCRIPT_DIR/getPackageName.py`;
echo "##[endgroup]";

echo "##[group] Building the main package";
python3 -m build -xnw .;
PACKAGE_FILE_NAME=$PACKAGE_NAME-0.CI-py3-none-any.whl;
PACKAGE_FILE_PATH=./dist/$PACKAGE_FILE_NAME;
mv ./dist/*.whl $PACKAGE_FILE_PATH;
echo "##[endgroup]";

echo "##[group] Installing the main package";
sudo pip3 install --upgrade $PACKAGE_FILE_PATH;
echo "##[endgroup]";
