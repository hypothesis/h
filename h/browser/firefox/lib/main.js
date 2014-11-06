const data = require("sdk/self").data;
const tabs = require("sdk/tabs");
const { ToggleButton } = require("sdk/ui/button/toggle");
var btn_config = {};
var btn;
// tab state machine
var tab_state = {};

function tabToggle(tab) {
  if (tab_state[tab.id] === true) {
    tab.attach({
      contentScriptFile: data.url('embed.js')
    });
  } else if (undefined === tab_state[tab.id] || tab_state[tab.id] === false) {
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
  icon: {
    "18": './images/sleeping_18.png',
    "32": './images/sleeping_32.png',
    "36": './images/sleeping_36.png',
    "64": './images/sleeping_64.png'
  },
  onChange: function() {
    // delete the window-wide state default
    this.state('window', null);
    // but turn it back on for this tab
    this.state('tab', {checked: !this.state('tab').checked});
    tab_state[tabs.activeTab.id] = this.state('tab').checked;
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
  tab_state[tab.id] = false;
});
