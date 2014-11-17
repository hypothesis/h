(function (h) {
  'use strict';

  /* The tab store ensures that the current state of the browser action
   * is persisted between browser sessions. To do this it uses an external
   * storage object that conforms to the localStorage API.
   *
   * Examples
   *
   *   var store = new TabStore(window.localStorage);
   */
  function TabStore(storage) {
    var key = 'state';
    var local;

    this.get = function (tabId) {
      var value = local[tabId];
      if (!value) {
        throw new Error('TabStateStore could not find entry for tab: ' + tabId);
      }
      return value;
    };

    this.set = function (tabId, value) {
      local[tabId] = value;
      storage.setItem(key, JSON.stringify(local));
    };

    this.unset = function (tabId) {
      delete local[tabId];
      storage.setItem(key, JSON.stringify(local));
    };

    this.all = function () {
      return local;
    };

    this.reload = function () {
      try {
        local = JSON.parse(storage.getItem(key));
      } catch (e) {
        local = null;
      }
      local = local || {};
    };

    this.reload();
  }

  h.TabStore = TabStore;
})(window.h || (window.h = {}));
