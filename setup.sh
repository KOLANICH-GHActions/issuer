set -e

for envVar in ${!ACTION_*};
do
unset $envVar;
done

for envVar in ${!GITHUB_*};
do
unset $envVar;
done

for envVar in ${!INPUT_*};
do
unset $envVar;
done

echo "##[group] Bootstrapping packaging"
git clone --depth=1 https://github.com/pypa/setuptools.git
cd ./setuptools
python3 ./bootstrap.py
sudo python3 ./setup.py install
cd ..
git clone --depth=1 https://github.com/pypa/pip.git
cd ./pip
sudo python3 -m pip install .
cd ..
cd ./setuptools
sudo python3 -m pip install .
cd ..
git clone --depth=1 https://github.com/pypa/wheel.git
cd wheel
sudo pip3 install .
cd ..
sudo rm -rf ./setuptools ./pip ./wheel
echo "##[endgroup]"

echo "##[group] Installing dependencies from apt"
sudo apt-get install -y python3-docutils
echo "##[endgroup]"

echo "##[group] Installing dependencies from git"
for repoURI in $(cat ./pythonPackagesToInstallFromGit.txt); do
    git clone --depth=1 $repoURI PKG_DIR;
    cd ./PKG_DIR;
    python3 ./setup.py bdist_wheel;
    sudo pip3 install --upgrade --pre ./dist/*.whl;
    cd ..;
    rm -rf ./PKG_DIR;
done;
echo "##[endgroup]"

echo "##[group] Installing the main package"
python3 ./setup.py bdist_wheel
sudo pip3 install --upgrade --pre ./dist/*
echo "##[endgroup]"
