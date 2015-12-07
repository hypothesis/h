// TODO - Make this a CommonJS module and move it into
// the site JS?
var env = {
  browserIsChrome: typeof window.chrome !== 'undefined',
  browserIsOther: typeof window.chrome === 'undefined',
};

function hypenate(key) {
  // 'camelCase' -> 'camel-case'
  return key.replace(/[a-z]+/g, '$&-').toLowerCase().slice(0, -1);
}

Object.keys(env).forEach(function (key) {
  var selector = '.js-' + hypenate(key);
  var elements = document.querySelectorAll(selector);
  for (var i = 0; i < elements.length; i++) {
    if (env[key]) {
      elements[i].classList.remove('is-hidden');
    } else {
      elements[i].classList.add('is-hidden');
    }
  }
});
