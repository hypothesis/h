// Defines a set of vendor bundles which are
// libraries of 3rd-party code referenced by
// one or more bundles of Hypothesis client/frontend
// code

/**
 * Decorate a module ID with a 'doNotParse' property
 * indicating that the module bundler should not try
 * to parse it for require() statements.
 */
function doNotParse(id) {
  return {
    name: id,
    noParse: true,
  };
}

module.exports = {
  jquery: [doNotParse('jquery')],
  bootstrap: [doNotParse('bootstrap')],
  polyfills: ['./h/static/scripts/polyfills'],
  angular: [
    'angular',
    'angular-animate',
    'angular-jwt',
    'angular-resource',
    'angular-route',
    'angular-sanitize',
    'ng-tags-input',
    'angular-toastr',
    'angulartics/src/angulartics',
    'angulartics/src/angulartics-ga'
  ],
  katex: [doNotParse('./h/static/scripts/vendor/katex')],
  showdown: ['showdown'],
  unorm: ['unorm'],
  raven: ['raven-js'],
};
