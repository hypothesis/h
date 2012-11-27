// http://my.opera.com/emoller/blog/2011/12/20/requestanimationframe-for-smart-er-animating
(function() {
  var pfx = ['ms', 'moz', 'webkit', 'o'];
  for (var i = 0; i < pfx.length && !window.requestAnimationFrame ; i++) {
    requestAnimationFrame = window[pfx[i]+'RequestAnimationFrame'];
    cancelAnimationFrame = window[pfx[i]+'CancelRequestAnimationFrame'];
    if (!cancelAnimationFrame) {
      cancelAnimationFrame = window[pfx[i]+'CancelAnimationFrame'];
    }
    window.requestAnimationFrame = requestAnimationFrame;
    window.cancelAnimationFrame = cancelAnimationFrame;
  }

  if (!window.requestAnimationFrame)
    var lastTime = 0;
    window.requestAnimationFrame = function(callback, element) {
      var currTime = new Date().getTime();
      var timeToCall = Math.max(0, 16 - (currTime - lastTime));
      var id = window.setTimeout(function() {
        callback(currTime + timeToCall);
      }, timeToCall);
      lastTime = currTime + timeToCall;
      return id;
    };

  if (!window.cancelAnimationFrame)
    window.cancelAnimationFrame = function(id) {
      clearTimeout(id);
    };
}())
