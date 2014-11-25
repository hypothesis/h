(function () {
  // Injects the hypothesis dependencies. These can be either js or css, the
  // file extension is used to determine the loading method. This file is
  // pre-processed in order to insert the wgxpath and inject scripts.
  //
  // Custom injectors can be provided to load the scripts into a different
  // environment. Both script and stylesheet methods are provided with a url
  // and a callback fn that expects either an error object or null as the only
  // argument.
  //
  // For example a Chrome extension may look something like:
  //
  //   window.hypothesisInstall({
  //     script: function (src, fn) {
  //       chrome.tabs.executeScript(tab.id, {file: src}, fn);
  //     },
  //     stylesheet: function (href, fn) {
  //       chrome.tabs.insertCSS(tab.id, {file: href}, fn);
  //     }
  //   });
  window.hypothesisInstall = function (inject) {
    inject = inject || {};

    var resources = [];
    var injectStylesheet = inject.stylesheet || function injectStylesheet(href, fn) {
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.type = 'text/css';
      link.href = href;

      document.head.appendChild(link);
      fn(null);
    };

    var injectScript = inject.script || function injectScript(src, fn) {
      var script = document.createElement('script');
      script.type = 'text/javascript';
      script.onload = function () { fn(null) };
      script.onerror = function () { fn(new Error('Failed to load script: ' + src)) };
      script.src = src;

      document.head.appendChild(script);
    };

    if (!window.document.evaluate) {
      resources = resources.concat(['{{ layout.xpath_polyfil_urls | map("string") | join("', '") | safe }}']);
    }

    if (typeof window.Annotator === 'undefined') {
      resources = resources.concat(['{{ layout.app_inject_urls | map("string") | join("', '") | safe }}']);
    }

    (function next(err) {
      if (err) { throw err; }

      if (resources.length) {
        var url = resources.shift();
        var ext = url.split('?')[0].split('.').pop();
        var fn = (ext === 'css' ? injectStylesheet : injectScript);
        fn(url, next);
      }
    })();
  }

  // Check for deployment conditions
  var isLocal = document.location.protocol == 'file:';
  var isPDF = document.location.pathname.toLowerCase().indexOf('.pdf') > 0;
  var hasPDFjs = window.PDFJS !== undefined

  // Check for file:// URLs, which are not supported, as of now.
  if (isLocal && !isPDF) {
    window.alert("Sorry, but as of now, this service can't be used on local HTMLs documents loaded via the file:/// protocol. (Local PDF documents are supported, though.)");
    return;
  }
  if (isPDF && !hasPDFjs) {
    window.alert("Annotating PDF documents is supported via the PDF.js software. In order to use it, you need a browser which ships PDF.js embedded (like Firefox), or you need the Hypothes.is Chrome extension.");
    return;
  }

  var baseUrl = document.createElement('link');
  baseUrl.rel = 'sidebar';
  baseUrl.href = '{{ base_url }}app.html';
  baseUrl.type = 'application/annotator+html';
  document.head.appendChild(baseUrl);

  window.hypothesisInstall();
})();
