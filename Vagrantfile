# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "private_network", ip: {{cookiecutter.domain_name}}
  config.vm.host_name = "{{cookiecutter.repo_name}}.dev"
  config.vm.provision :shell, :path => ".provision/vagrant_setup.sh"
  config.vm.define {{cookiecutter.repo_name}}
end
