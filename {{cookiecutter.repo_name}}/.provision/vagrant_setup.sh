#!/bin/bash
PROJECT_NAME={{cookiecutter.repo_name}}
PROJECT_HOST_NAME={{cookiecutter.domain_name}}
VM_IP={{cookiecutter.vm_ip}}
VIRTUALENV_DIR=/sites
USER_HOME=/home/vagrant
PROJECT_SOURCE=${VIRTUALENV_DIR}/${PROJECT_NAME}/source

echo "Environment installation is beginning. This may take a few minutes.."

echo "Installing required packages.."
apt-get -y install git mc

echo "Installing and upgrading pip.."
apt-get -y install python-setuptools
easy_install -U pip

echo "Installing required packages for postgres.."
apt-get -y install postgresql

echo "Installing required packages for python package 'psycopg2'.."
apt-get -y install python-dev python3-dev libpq-dev

echo "Installing virtualenvwrapper from pip.."
pip install virtualenvwrapper fabric

{% if cookiecutter.dotfile_configs_repo_url -%}
git clone {{cookiecutter.dotfile_configs_repo_url}} && sudo su - vagrant /bin/bash -c "set -- -f; source ~/dotfiles/bootstrap.sh"
{%- endif %}

echo "WORKON_HOME=${VIRTUALENV_DIR}" >> ${USER_HOME}/.bash_profile
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ${USER_HOME}/.bash_profile

echo "Install the virtual environment.."
mkdir ${VIRTUALENV_DIR}
chown vagrant:vagrant ${VIRTUALENV_DIR}
sudo su - vagrant /bin/bash -c "\
   mkvirtualenv --python=`which python3` ${PROJECT_NAME};\
   ln -s /vagrant ${PROJECT_SOURCE};\
   pip install -r ${PROJECT_SOURCE}/requirements/local.txt"

echo "cd ${PROJECT_SOURCE}" >> ${USER_HOME}/.bash_profile
echo "workon ${PROJECT_NAME}" >> ${USER_HOME}/.bash_profile

echo "Configuring postgres.."
sudo -u postgres psql -c "create user ${PROJECT_NAME} with password '${PROJECT_NAME}';"
sudo -u postgres psql -c "create database ${PROJECT_NAME};"
sudo -u postgres psql -c "grant all privileges on database ${PROJECT_NAME} to ${PROJECT_NAME};"

echo "Setting current django config.."
sudo su - vagrant /bin/bash -c "cd ${PROJECT_NAME}; ln -sf settings/dev.py current_settings.py"

echo ""
echo "==============================="
echo "=            Done!            ="
echo "==============================="
