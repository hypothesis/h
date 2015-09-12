Sidebar = require('./sidebar')


module.exports = class PdfSidebar extends Sidebar
  options:
    TextSelection: {}
    Pdf: {}
    BucketBar:
      container: '.annotator-frame'
      scrollables: ['#viewerContainer']
    Toolbar:
      container: '.annotator-frame'
