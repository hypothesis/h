WebFontConfig = {
  google: {
    families: [
      'Merriweather',
      'Source+Sans+Pro:400,600:latin,latin-ext'
    ]
  }
};
(function() {
  var wf = document.createElement('script');
  wf.src = 'https://ajax.googleapis.com/ajax/libs/webfont/1/webfont.js';
  wf.type = 'text/javascript';
  wf.async = 'true';
  var s = document.getElementsByTagName('script')[0];
  s.parentNode.insertBefore(wf, s);
})();
