var Klass = window.Annotator.Host;
var docs = 'https://github.com/hypothesis/h/blob/master/README.rst#customized-embedding'
var options = {
  app: $('link[type="application/annotator+html"]').attr('href'),
  Heatmap: {container: '.annotator-frame'},
  Toolbar: {container: '.annotator-frame'}
}

if (window.hasOwnProperty('hypothesisRole')) {
  if (typeof window.hypothesisRole === 'function') {
    Klass = window.hypothesisRole;
  } else {
    throw new TypeError('hypothesisRole must be a constructor function, see: ' + docs);
  }
}

if (window.hasOwnProperty('hypothesisConfig')) {
  if (typeof window.hypothesisConfig === 'function') {
    options = window.hypothesisConfig();
  } else {
    throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
  }
}

window.annotator = new Klass(document.body, options);
window.Annotator.noConflict().$.noConflict(true);
