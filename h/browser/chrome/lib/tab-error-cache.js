(function (h) {
  'use strict';

  /* A wrapper around an Object for storing and retrieving error objects
   * created when trying to inject the Sidebar into the document. This
   * primarily exists to simplify the testing of the error handling. As
   * the setters/getters can easily be stubbed.
   */
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
