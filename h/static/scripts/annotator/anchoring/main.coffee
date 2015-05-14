if (window.PDFViewerApplication)
  module.exports = require('./pdf')
else
  module.exports = require('./html')
