var Annotator = require('annotator');

// Scroll plugin for jQuery
// TODO: replace me
require('jquery-scrollintoview')

// Polyfills
var g = Annotator.Util.getGlobal();
if (g.wgxpath) g.wgxpath.install();

require('node-iterator-shim').install();

// Applications
Annotator.Guest = require('./guest')
Annotator.Host = require('./host')

// Cross-frame communication
Annotator.Plugin.CrossFrame = require('./plugin/cross-frame')
Annotator.Plugin.CrossFrame.Bridge = require('../bridge')
Annotator.Plugin.CrossFrame.AnnotationSync = require('../annotation-sync')
Annotator.Plugin.CrossFrame.Discovery = require('../discovery')

// Bucket bar
require('./plugin/bucket-bar');

// Toolbar
require('./plugin/toolbar');

// Creating selections
require('./plugin/textselection');


var docs = 'https://h.readthedocs.org/en/latest/hacking/customized-embedding.html';
var options = {
  app: jQuery('link[type="application/annotator+html"]').attr('href'),
  BucketBar: {container: '.annotator-frame', scrollables: ['body']},
  Toolbar: {container: '.annotator-frame'}
};

// Document metadata plugins
if (window.PDFViewerApplication) {
  require('./plugin/pdf')
  options['BucketBar']['scrollables'] = ['#viewerContainer']
  options['PDF'] = {};
} else {
  require('../vendor/annotator.document');
  options['Document'] = {};
}

if (window.hasOwnProperty('hypothesisConfig')) {
  if (typeof window.hypothesisConfig === 'function') {
    options = jQuery.extend(options, window.hypothesisConfig());
  } else {
    throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
  }
}

Annotator.noConflict().$.noConflict(true)(function () {
  var Klass = Annotator.Host;
  if (options.hasOwnProperty('constructor')) {
    Klass = options.constructor;
    delete options.constructor;
  }
  window.annotator = new Klass(document.body, options);
});
