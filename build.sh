#!/usr/bin/env bash

rm -r ./anopcb-2.0.0/usr/share/kicad/scripting/plugins/AnomalyPlugin

mkdir -p ./anopcb-2.0.0/usr/share/kicad/scripting/plugins/AnomalyPlugin
cp -r ./AnomalyPlugin/* ./anopcb-2.0.0/usr/share/kicad/scripting/plugins/AnomalyPlugin
rm -r ./anopcb-2.0.0/usr/share/kicad/scripting/plugins/AnomalyPlugin/__pycache__
rm -r ./anopcb-2.0.0/usr/share/kicad/scripting/plugins/AnomalyPlugin/.vscode
rm ./anopcb-2.0.0/usr/share/kicad/scripting/plugins/AnomalyPlugin/pip_requirements.txt

dpkg -b ./anopcb-2.0.0 ./anopcb_2.0.0.deb

mkdir ./rpm
cp ./anopcb_2.0.0.deb ./rpm/
cd ./rpm
alien --scripts -r anopcb_2.0.0.deb
cd ..
mv ./rpm/anopcb-2.0.0-2.noarch.rpm ./
rm -r ./rpm
