var base = $('link').filter(function () {
  return this.type == 'application/annotator+html';
}).attr('href');
var klass = window.hypothesisRole || window.Annotator.Host, options = {};
(window.hypothesisConfig || (function () {
  this.app = base;
  this.Heatmap = {container: '.annotator-frame'};
  this.Toolbar = {container: '.annotator-frame'};
})).call(options);
window.annotator = new klass(document.body, options);
window.Annotator.noConflict().$.noConflict(true);
