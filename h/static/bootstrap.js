var Annotator = require('annotator');

// Monkeypatch annotator!
require('./scripts/annotator/monkey');

// Cross-frame communication
require('./scripts/annotator/plugin/cross-frame');
require('./scripts/annotation-sync');
require('./scripts/bridge');
require('./scripts/discovery');

// Document plugin
require('./scripts/vendor/annotator.document');

// Bucket bar
require('./scripts/annotator/plugin/bucket-bar');

// Toolbar
require('./scripts/annotator/plugin/toolbar');

// Drawing highlights
require('./scripts/annotator/plugin/texthighlights');

// Creating selections
require('./scripts/annotator/plugin/textselection');

// URL fragments
require('./scripts/annotator/plugin/fragmentselector');

// Anchoring
require('./scripts/vendor/dom_text_mapper');
require('./scripts/annotator/plugin/enhancedanchoring');
require('./scripts/annotator/plugin/domtextmapper');
require('./scripts/annotator/plugin/textposition');
require('./scripts/annotator/plugin/textquote');
require('./scripts/annotator/plugin/textrange');

// PDF
require('./scripts/vendor/page_text_mapper_core');
require('./scripts/annotator/plugin/pdf');

// Fuzzy
require('./scripts/vendor/dom_text_matcher');
require('./scripts/annotator/plugin/fuzzytextanchors');

var Klass = require('./scripts/host');
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

if (window.hasOwnProperty('hypothesisConfig')) {
  if (typeof window.hypothesisConfig === 'function') {
    options = jQuery.extend(options, window.hypothesisConfig());
  } else {
    throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
  }
}

window.annotator = new Klass(document.body, options);
Annotator.noConflict().$.noConflict(true);
