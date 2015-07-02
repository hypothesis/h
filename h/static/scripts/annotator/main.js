var Annotator = require('annotator');

// Monkeypatch annotator!
require('./monkey');

// Applications
Annotator.Guest = require('./guest')
Annotator.Host = require('./host')

// Cross-frame communication
Annotator.Plugin.CrossFrame = require('./plugin/cross-frame')
Annotator.Plugin.CrossFrame.Bridge = require('../bridge')
Annotator.Plugin.CrossFrame.AnnotationSync = require('../annotation-sync')
Annotator.Plugin.CrossFrame.Discovery = require('../discovery')

// Document plugin
require('../vendor/annotator.document');

// Bucket bar
require('./plugin/bucket-bar');

// Toolbar
require('./plugin/toolbar');

// Drawing highlights
require('./plugin/texthighlights');

// Creating selections
require('./plugin/textselection');

// URL fragments
require('./plugin/fragmentselector');

// Anchoring dependencies
require('diff-match-patch')
require('dom-text-mapper')
require('dom-text-matcher')
require('page-text-mapper-core')
require('text-match-engines')

// Anchoring plugins
require('./plugin/enhancedanchoring');
require('./plugin/domtextmapper');
require('./plugin/fuzzytextanchors');
require('./plugin/pdf');
require('./plugin/textquote');
require('./plugin/textposition');
require('./plugin/textrange');

var docs = 'https://h.readthedocs.org/en/latest/hacking/customized-embedding.html';
var options = {
  app: jQuery('link[type="application/annotator+html"]').attr('href'),
  BucketBar: {container: '.annotator-frame'},
  Toolbar: {container: '.annotator-frame'}
};

// Simple IE autodetect function
// See for example https://stackoverflow.com/questions/19999388/jquery-check-if-user-is-using-ie/21712356#21712356
var ua = window.navigator.userAgent;
if ((ua.indexOf("MSIE ") > 0) ||     // for IE <=10
    (ua.indexOf('Trident/') > 0) ||  // for IE 11
    (ua.indexOf('Edge/') > 0)) {     // for IE 12
  options["DomTextMapper"] = {"skip": true}
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
