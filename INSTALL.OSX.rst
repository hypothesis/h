Installing Hypothes.is on OS X ML
######################

Install Homebrew::

    $ ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"

Install python::
    
    $ brew install python

Install virtualenv::
    
    $ pip install virtualenv
    $ sudo ln /usr/local/share/python/virtualenv /usr/bin/virtualenv

Install Node and other required tools::

    $ sudo gem install compass
    $ brew install node
    $ sudo npm -g install uglify-js
    $ sudo npm -g install handlebars
    $ sudo npm -g install coffee-script

Add the tools' path to the $PATH variable::

    $ vim ~/.profile
    $ add '/usr/local/share/npm/bin' to the PATH variable e.g. export PATH=/usr/local/share/npm/bin:/usr/local/bin:$PATH
    $ source ~/.profile

Install Elasticsearch::

    $ brew install elasticsearch
    
To have Elasticsearch run automatically at login::

    $ ln -sfv /usr/local/opt/elasticsearch/*.plist ~/Library/LaunchAgents
    $ launchctl load ~/Library/LaunchAgents/homebrew.mxcl.elasticsearch.plist
    
To launch it manually without launchctl::

    $ elasticsearch -f -D es.config=/usr/local/opt/elasticsearch/config/elasticsearch.yml

After installing the above, create the virtualenv, as described in the README.rst

(Run the commands from the directory where you've cloned the repository.)