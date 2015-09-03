#!/bin/bash
PROJECT_NAME=$1
PROJECT_HOST_NAME=$2
VM_IP=$3
VIRTUALENV_DIR=/sites
PROJECT_SOURCE=${VIRTUALENV_DIR}/${PROJECT_NAME}/source
USER_HOME=/home/vagrant

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

#git clone https://github.com/cubicuboctahedron/dotfiles.git && sudo su - vagrant /bin/bash -c "set -- -f; source ~/dotfiles/bootstrap.sh"

echo "WORKON_HOME=${VIRTUALENV_DIR}" >> ${USER_HOME}/.bash_profile
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ${USER_HOME}/.bash_profile
echo "cd ${PROJECT_SOURCE}" >> ${USER_HOME}/.bash_profile

echo "Install the virtual environment.."
mkdir ${VIRTUALENV_DIR}
chown vagrant:vagrant ${VIRTUALENV_DIR}
sudo su - vagrant /bin/bash -c "\
    mkvirtualenv --python=`which python3` ${PROJECT_NAME};\
    ln -s /vagrant ${PROJECT_SOURCE};\
    pip install -r ${PROJECT_SOURCE}/requirements.txt"

echo "workon ${PROJECT_NAME}" >> ${USER_HOME}/.bash_profile

echo "Configuring postgres.."
sudo -u postgres psql -c "create user ${PROJECT_NAME} with password '{$PROJECT_NAME}';"
sudo -u postgres psql -c "create database dev.${PROJECT_NAME};"
sudo -u postgres psql -c "grant all privileges on database dev.${PROJECT_NAME} to ${PROJECT_NAME};"

echo "Changing django project name.."
sudo su - vagrant /bin/bash -c "\
    git mv project_name/project_name project_name/${PROJECT_NAME}\
    git mv project_name ${PROJECT_NAME}"

echo "Updating django configs.."
sudo su - vagrant /bin/bash -c "\
    sed -i 's/PROJECT_NAME/${PROJECT_NAME}/g' ${PROJECT_NAME}/settings/*.py;\
    sed -i 's/PROJECT_HOST_NAME/${PROJECT_HOST_NAME}/g' ${PROJECT_NAME}/settings/*.py;\
    sed -i 's/VIRTUAL_MACHINE_IP/${VM_IP}/g' ${PROJECT_NAME}/settings/*.py;"

echo "Setting current django config.."
sudo su - vagrant /bin/bash -c "ln -s ${PROJECT_NAME}/${PROJECT_NAME}/settings/dev.py ${PROJECT_NAME}/${PROJECT_NAME}/current_settings.py"

echo "==============================="
echo "Done!"
echo "You may now change repo's origin url (if you cloned this repository), commit and push all changes done."
echo "==============================="
