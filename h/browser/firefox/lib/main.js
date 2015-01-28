const self = require("sdk/self");
const data = self.data;
const tabs = require("sdk/tabs");
const { ToggleButton } = require("sdk/ui/button/toggle");
var bgScriptDidLoad = false;
var btn_config = {};
var btn;

// NOTE: The 18 and 36 icons are actually 16x16 and 32x32 respectively as
// FireFox will downscale 18x18 icons. I can't find any documentation on
// on why this happens or how to prevent this.
var icons = {
  'sleeping': {
    "18": data.url('images/toolbar-inactive.png'),
    "32": data.url('images/menu-item.png'),
    "36": data.url('images/toolbar-inactive@2x.png'),
    "64": data.url('images/menu-item@2x.png')
  },
  // for all occasionas
  'active': {
    "18": data.url('images/toolbar-active.png'),
    "32": data.url('images/menu-item.png'),
    "36": data.url('images/toolbar-active@2x.png'),
    "64": data.url('images/menu-item@2x.png')
  }
};

function enable(tab) {
  tab.attach({
    contentScript: [
      'var s = document.createElement("script");',
      's.setAttribute("src", "' + data.url('embed.js') + '");',
      'document.body.appendChild(s);'
    ]
  });
}

function disable(tab) {
  tab.attach({
    contentScript: [
      'var s = document.createElement("script");',
      's.setAttribute("src", "' + data.url('destroy.js') + '");',
      'document.body.appendChild(s);'
    ]
  });
}

function activate(btn, tab) {
  btn.state(tab, {
    checked: true,
    label: 'Annotating',
    icon: icons.active
  });
}

function deactivate(btn, tab) {
  btn.state(tab, {
    checked: false,
    label: 'Annotate',
    icon: icons.sleeping
  });
}

btn_config = {
  id: "hypothesis",
  label: "Annotate",
  icon: icons.sleeping,
  onClick: function (state) {
    // delete the window-wide state default
    this.state('window', null);
    // but turn it back on for this tab
    if (this.state(tabs.activeTab).checked !== true) {
      activate(btn, tabs.activeTab);
      enable(tabs.activeTab);
    } else {
      deactivate(btn, tabs.activeTab);
      disable(tabs.activeTab);
    }
  }
};

if (undefined === ToggleButton) {
  btn = require("sdk/widget").Widget(btn_config);
} else {
  btn = ToggleButton(btn_config);
}

tabs.on('pageshow', function onPageShow(tab) {
  if (btn.state(tab).checked) {
    enable(tab);
  } else {
    disable(tab);
  }
});

tabs.on('open', function onTabOpen(tab) {
  // h is off by default on new tabs
  deactivate(btn, tab);
});

exports.main = function main(options, callbacks) {
  if (options.loadReason === 'install') {
    tabs.open({
      url: 'https://hypothes.is/welcome',
      onReady: function (tab) {
        activate(btn, tab);
      }
    });
  }
};

exports.onUnload = function onUnload(reason) {
  if (reason === 'uninstall' || reason === 'disable') {
    [].forEach.call(tabs, disable);
  }
};
