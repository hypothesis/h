Installing Hypothes.is on OS X ML
######################

Install Homebrew::

``` bash
ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"
```

Install python::

``` bash
brew install python
```

Install virtualenv::

``` bash
pip install virtualenv
```

Install Node and other required tools::

``` bash
gem install compass
brew install node
npm -g install uglify-js handlebars coffee-script
```

Add the tools' path to the $PATH variable::

``` bash
echo "export PATH=/usr/local/share/python:$PATH" >> ~/.profile
echo "export PATH=/usr/local/share/npm/bin:$PATH" >> ~/.profile
```

Install Elasticsearch::

``` bash
brew install elasticsearch
```

To have Elasticsearch run automatically at login::

``` bash
ln -sfv /usr/local/opt/elasticsearch/*.plist ~/Library/LaunchAgents
launchctl load ~/Library/LaunchAgents/homebrew.mxcl.elasticsearch.plist
```

To launch it manually without launchctl::

``` bash
elasticsearch -f -D es.config=/usr/local/opt/elasticsearch/config/elasticsearch.yml
```

After installing the above, create the virtualenv, as described in the INSTALL.rst

(Run the commands from the directory where you've cloned the repository.)
