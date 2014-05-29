var loadH = "var d=document, s=d.createElement('script'); s.setAttribute('src','https://hypothes.is/embed.js'); d.body.appendChild(s);";

/*
var pageMod = require('sdk/page-mod');
pageMod.PageMod({
  include: '*',
  contentScript: loadH
});
*/

var widgets = require("sdk/widget");
var tabs = require("sdk/tabs");

var widget = widgets.Widget({
  id: "hypothesis",
  label: "Annotate",
  contentURL: "http://hypothes.is/wp-content/uploads/2012/12/favicon1.ico",
  onClick: function() {
    tabs.activeTab.attach({
      contentScript: loadH
    });
  }
});
