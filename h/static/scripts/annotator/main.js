var extend = require('extend');
var Annotator = require('annotator');

// Polyfills
var g = Annotator.Util.getGlobal();
if (g.wgxpath && !g.document.evaluate) {
  g.wgxpath.install();
}

// Applications
Annotator.Guest = require('./guest');
Annotator.Host = require('./host');
Annotator.Sidebar = require('./sidebar');
Annotator.PdfSidebar = require('./pdf-sidebar');

// UI plugins
Annotator.Plugin.BucketBar = require('./plugin/bucket-bar');
Annotator.Plugin.Toolbar = require('./plugin/toolbar');

// Document type plugins
Annotator.Plugin.PDF = require('./plugin/pdf');
require('../vendor/annotator.document');  // Does not export the plugin :(

// Selection plugins
Annotator.Plugin.TextSelection = require('./plugin/textselection');

// Cross-frame communication
Annotator.Plugin.CrossFrame = require('./plugin/cross-frame');
Annotator.Plugin.CrossFrame.AnnotationSync = require('../annotation-sync');
Annotator.Plugin.CrossFrame.Bridge = require('../bridge');
Annotator.Plugin.CrossFrame.Discovery = require('../discovery');

var docs = 'https://h.readthedocs.org/en/latest/hacking/customized-embedding.html';
var options = {
  app: jQuery('link[type="application/annotator+html"]').attr('href')
};

if (window.hasOwnProperty('hypothesisConfig')) {
  if (typeof window.hypothesisConfig === 'function') {
    extend(options, window.hypothesisConfig());
  } else {
    throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
  }
}

Annotator.noConflict().$.noConflict(true)(function() {
  'use strict';
  var Klass = window.PDFViewerApplication ?
      Annotator.PdfSidebar :
      Annotator.Sidebar;
  if (options.hasOwnProperty('constructor')) {
    Klass = options.constructor;
    delete options.constructor;
  }
  window.annotator = new Klass(document.body, options);
});
