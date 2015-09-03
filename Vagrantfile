# -*- mode: ruby -*-
# vi: set ft=ruby :

PROJECT_NAME = "project"
PROJECT_HOST_NAME = PROJECT_NAME+".com"
IP = "10.10.10.100"

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "private_network", ip: IP
  config.vm.host_name = PROJECT_NAME+".dev"
  config.vm.provision :shell, :path => ".install/vagrant_setup.sh", :args => [PROJECT_NAME, PROJECT_HOST_NAME, IP]

  config.vm.define PROJECT_NAME

end
