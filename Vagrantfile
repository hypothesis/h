# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# This vagrant file will create a Ubuntu LTS VM with the h package and dependencies installed and the server
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

BOX_NAME = ENV['BOX_NAME'] || "precise32"
BOX_URI = ENV['BOX_URI'] || "http://files.vagrantup.com/precise32.box"
AWS_REGION = ENV['AWS_REGION'] || "us-east-1"
AWS_AMI    = ENV['AWS_AMI']    || "ami-d13d4bb8"

# Elasticsearch version.
# Note that vagrant destroy is required to get elasticsearch to be re-downloaded
$elversion="elasticsearch-1.1.1"

$script = <<SCRIPT
  apt-get update -qq
  apt-get -y install build-essential git libyaml-dev
  apt-get -y install python-{dev,pip,virtualenv,software-properties}
  apt-get -y install openjdk-7-jre
  add-apt-repository ppa:chris-lea/node.js
  apt-get update -qq
  apt-get -y install nodejs
  npm --quiet install --global coffee-script uglify-js
  gem install -y --no-ri --no-rdoc sass compass
  if test ! -s #{$elversion}.deb; then
    wget -q https://download.elasticsearch.org/elasticsearch/elasticsearch/#{$elversion}.deb
    dpkg -i #{$elversion}.deb
  fi
SCRIPT


Vagrant::Config.run do |config|
  config.vm.box = BOX_NAME
  config.vm.box_url = BOX_URI
  config.vm.forward_port 5000, 5000
  config.vm.share_folder "h", "/h", "."
  config.vm.provision :shell, :inline=>$script
end


# Providers were added on Vagrant >= 1.1.0
Vagrant::VERSION >= "1.1.0" and Vagrant.configure("2") do |config|
  config.vm.provider :aws do |aws, override|
    aws.access_key_id = ENV["AWS_ACCESS_KEY_ID"]
    aws.secret_access_key = ENV["AWS_SECRET_ACCESS_KEY"]
    aws.keypair_name = ENV["AWS_KEYPAIR_NAME"]
    override.ssh.private_key_path = ENV["AWS_SSH_PRIVKEY"]
    override.ssh.username = "ubuntu"
    aws.region = AWS_REGION
    aws.ami    = AWS_AMI
    aws.instance_type = "t1.micro"
  end

  config.vm.provider :rackspace do |rs|
    config.ssh.private_key_path = ENV["RS_PRIVATE_KEY"]
    rs.username = ENV["RS_USERNAME"]
    rs.api_key  = ENV["RS_API_KEY"]
    rs.public_key_path = ENV["RS_PUBLIC_KEY"]
    rs.flavor   = /512MB/
    rs.image    = /Ubuntu/
  end

  config.vm.provider :virtualbox do |vb|
    config.vm.box = BOX_NAME
    config.vm.box_url = BOX_URI
  end

  config.vm.provider :lxc do |lxc|
    config.vm.box = BOX_NAME
    config.vm.box_url = BOX_URI
    lxc.customize 'cgroup.memory.limit_in_bytes', '1024M'
  end
end
