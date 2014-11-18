(function (h) {
  function TabErrorCache() {
    var cache = {};

    this.getTabError = function (tabId, err) {
      return cache[tabId] || null;
    };

    this.setTabError = function (tabId, err) {
      cache[tabId] = err;
    };

    this.unsetTabError = function (tabId) {
      delete cache[tabId];
    };
  }
  h.TabErrorCache = TabErrorCache;
})(window.h || (window.h = {}));
