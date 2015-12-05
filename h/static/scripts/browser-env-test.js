var isMobile = navigator.userAgent.match(/\b(Mobile)\b/);
var isMicrosoftEdge = navigator.userAgent.match(/\bEdge\b/);

/**
 * Dictionary defining the conditions that can be used
 * to show or hide elements on the page depending on
 * features of the app or site that are available
 * in the current environment.
 *
 * Keys correspond to hyphenated class names prefixed with 'js-env',
 * eg. 'js-env-browser-is-chrome'.
 */
var env = {
  browserIsChrome: typeof window.chrome !== 'undefined',
  browserIsOther: typeof window.chrome === 'undefined',
  installerAvailable: !isMobile && !isMicrosoftEdge,
};

function hypenate(key) {
  // 'camelCase' -> 'camel-case'
  return key.replace(/[a-z]+/g, '$&-').toLowerCase().slice(0, -1);
}

/**
 * Show or hide elements on the page depending on the capabilities
 * of the current browser.
 *
 * Elements to be shown or hidden are marked up with
 * 'js-env-$condition' classes. If all conditions evaluate to true,
 * the 'is-hidden' class is removed from the element, otherwise
 * it is added.
 *
 * The list of conditions is defined by hyphenated versions of the
 * keys of the 'env' dictionary.
 */
function showSupportedElements(rootElement) {
  var showElements = [];
  var hideElements = [];

  Object.keys(env).forEach(function (key) {
    var selector = '.js-env-' + hypenate(key);
    var elements = rootElement.querySelectorAll(selector);
    for (var i = 0; i < elements.length; i++) {
      if (env[key]) {
        showElements.push(elements[i]);
      } else {
        hideElements.push(elements[i]);
      }
    }
  });

  showElements.forEach(function (el) {
    el.classList.remove('is-hidden');
  });
  hideElements.forEach(function (el) {
    el.classList.add('is-hidden');
  });
}

module.exports = {
  showSupportedElements: showSupportedElements,
};
