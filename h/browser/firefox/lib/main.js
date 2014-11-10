const data = require("sdk/self").data;
const tabs = require("sdk/tabs");
const { ToggleButton } = require("sdk/ui/button/toggle");
var btn_config = {};
var btn;

// NOTE: The 18 and 36 icons are actually 16x16 and 32x32 respectively as
// FireFox will downscale 18x18 icons. I can't find any documentation on
// on why this happens or how to prevent this.
var icons = {
  'sleeping': {
    "18": './images/toolbar-inactive.png',
    "32": './images/menu-item.png',
    "36": './images/toolbar-inactive@2x.png',
    "64": './images/menu-item@2x.png'
  },
  // for all occasionas
  'active': {
    "18": './images/toolbar-active.png',
    "32": './images/menu-item.png',
    "36": './images/toolbar-active@2x.png',
    "64": './images/menu-item@2x.png'
  }
};

function tabToggle(tab) {
  if (btn.state(tab).checked) {
    tab.attach({
      contentScriptFile: data.url('embed.js')
    });
  } else {
    tab.attach({
      contentScript: [
        'var s = document.createElement("script");',
        's.setAttribute("src", "' + data.url('destroy.js') + '");',
        'document.body.appendChild(s);'
      ]
    });
  }
}

btn_config = {
  id: "hypothesis",
  label: "Annotate",
  icon: icons['sleeping'],
  onChange: function() {
    // delete the window-wide state default
    this.state('window', null);
    // but turn it back on for this tab
    if (!this.state(tabs.activeTab).checked === true) {
      this.state(tabs.activeTab, {
        checked: true,
        label: 'Annotating',
        icon: icons['active']
      });
    } else {
      this.state(tabs.activeTab, {
        checked: false,
        label: 'Annotate',
        icon: icons['sleeping']
      });
    }
    tabToggle(tabs.activeTab)
  }
};

if (undefined === ToggleButton) {
  btn = require("sdk/widget").Widget(btn_config);
} else {
  btn = ToggleButton(btn_config);
}

tabs.on('pageshow', tabToggle);
tabs.on('open', function(tab) {
  // h is off by default on new tabs
  btn.state(tab).checked = false;
});
