# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# This vagrant file will create a Ubuntu LTS VM with the H package and dependencies installed and the server
# started and bridged to localhost:8080.
#
# Relevant commands (performed from this directory):
#
#    $vagrant up        # start the VM
#    $vagrant ssh       # shell into the VM
#    $vagrant halt      # bring the VM down, preserving state
#    $vagrant destroy   # destroy the VM (and any changed state)
#
# See vagrantup.com for more details on vagrant
# See the INSTALL files for an explanation of what is happening below.

# Elasticsearch version.
# Note that vagrant destroy is required to get elasticsearch to be re-downloaded
$elversion="elasticsearch-0.20.6"

$script = <<SCRIPT
  apt-get update -qq
  apt-get -y install python-{dev,pip,virtualenv,software-properties} git libpq-dev openjdk-7-jre
  add-apt-repository ppa:chris-lea/node.js
  apt-get update -qq
  apt-get -y install nodejs
  npm --quiet install --global coffee-script uglify-js
  gem install -y sass compass
  if test ! -s #{$elversion}.deb; then
    wget -q https://download.elasticsearch.org/elasticsearch/elasticsearch/#{$elversion}.deb
    dpkg -i #{$elversion}.deb
  fi
SCRIPT



Vagrant.configure("2") do |config|
  config.vm.box = "precise32"
  config.vm.box_url = "http://files.vagrantup.com/precise32.box"
  config.vm.network :forwarded_port, guest: 80, host: 8080   # general purpose
  config.vm.network :forwarded_port, guest: 5000, host: 5000 # h server
  config.vm.synced_folder ".", "/h"
  config.vm.provision :shell, :inline=>$script
end
