var data = require("sdk/self").data;
var tabs = require("sdk/tabs");
var { ToggleButton } = require("sdk/ui/button/toggle");
var btn_config = {};
var btn;

function tabToggle(tab) {
  if (btn.state('window').checked) {
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
  contentURL: "http://hypothes.is/wp-content/uploads/2012/12/favicon1.ico",
  icon: {
    "18": './images/sleeping_18.png',
    "32": './images/sleeping_32.png',
    "36": './images/sleeping_36.png',
    "64": './images/sleeping_64.png'
  },
  onClick: function(state) {
    tabToggle(tabs.activeTab)
  }
};

if (undefined === ToggleButton) {
  btn = require("sdk/widget").Widget(btn_config);
} else {
  btn = ToggleButton(btn_config);
}

tabs.on('open', function(tab) {
  tab.on('activate', tabToggle);
  tab.on('pageshow', tabToggle);
});
