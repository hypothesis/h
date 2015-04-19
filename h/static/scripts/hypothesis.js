var Annotator = require('annotator');

// Monkeypatch annotator!
require('./annotator/monkey');

// Applications
Annotator.Guest = require('./annotator/guest')
Annotator.Host = require('./annotator/host')

// Cross-frame communication
Annotator.Plugin.CrossFrame = require('./annotator/plugin/cross-frame')
Annotator.Plugin.CrossFrame.Bridge = require('./bridge')
Annotator.Plugin.CrossFrame.AnnotationSync = require('./annotation-sync')
Annotator.Plugin.CrossFrame.Discovery = require('./discovery')

// Document plugin
require('./vendor/annotator.document');

// Bucket bar
require('./annotator/plugin/bucket-bar');

// Toolbar
require('./annotator/plugin/toolbar');

// Drawing highlights
require('./annotator/plugin/texthighlights');

// Creating selections
require('./annotator/plugin/textselection');

// URL fragments
require('./annotator/plugin/fragmentselector');

// Anchoring dependencies
require('diff-match-patch')
require('dom-text-mapper')
require('dom-text-matcher')
require('page-text-mapper-core')
require('text-match-engines')

// Anchoring plugins
require('./annotator/plugin/enhancedanchoring');
require('./annotator/plugin/domtextmapper');
require('./annotator/plugin/fuzzytextanchors');
require('./annotator/plugin/pdf');
require('./annotator/plugin/textquote');
require('./annotator/plugin/textposition');
require('./annotator/plugin/textrange');

var Klass = Annotator.Host;
var docs = 'https://github.com/hypothesis/h/blob/master/README.rst#customized-embedding';
var options = {
  app: jQuery('link[type="application/annotator+html"]').attr('href'),
  BucketBar: {container: '.annotator-frame'},
  Toolbar: {container: '.annotator-frame'}
};

if (window.hasOwnProperty('hypothesisRole')) {
  if (typeof window.hypothesisRole === 'function') {
    Klass = window.hypothesisRole;
  } else {
    throw new TypeError('hypothesisRole must be a constructor function, see: ' + docs);
  }
}

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
  window.annotator = new Klass(document.body, options);
});
