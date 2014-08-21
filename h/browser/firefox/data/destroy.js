var terminate = [
  'if (window.annotator) window.annotator.destroy();',
  'delete window.annotator;',
  'delete window.DomTextMapper;',
  'delete window.DomTextMatcher;'
].join('\n')
, script = document.createElement('script')
, first = document.getElementsByTagName('script')[0]
, isGecko = ("MozAppearance" in document.documentElement.style)
, isGeckoLTE18 = isGecko && !! document.createRange().compareNode
, insBeforeObj = isGeckoLTE18 ? document.documentElement : first ? first.parentNode : document.documentElement.firstChild
;
script.text = terminate;
insBeforeObj.insertBefore(script, first);
delete window.hypothesisHasRun;
