#!/usr/bin/bash
sudo apt update
sudo apt install software-properties-common

echo "ppa added"

sudo add-apt-repository ppa:deadsnakes/ppa

echo "installing python3.8"
sudo apt install python3.8-distutils

echo "installing virtualenv"
sudo apt install virtualenv

echo "setting up virtual env"
virtualenv -p python3.8 env

echo "activating environment"
source env/bin/activate

echo "installing requiremnts"
pip install --requirement requirements.txt

echo "Setup complete" 
echo "to set your API key: export API_KEY=<api_key_from_iex_cloud>"
echo "to run the app: flask run"
