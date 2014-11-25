/**
* @author Jason Dobry <jason.dobry@gmail.com>
* @file angular-cache.js
* @version 3.2.2 - Homepage <https://github.com/jmdobry/angular-cache>
* @copyright (c) 2013-2014 Jason Dobry <http://www.pseudobry.com>
* @license MIT <https://github.com/jmdobry/angular-cache/blob/master/LICENSE>
*
* @overview angular-cache is a very useful replacement for Angular's $cacheFactory.
*/
(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
/**
 * @method bubbleUp
 * @param {array} heap The heap.
 * @param {function} weightFunc The weight function.
 * @param {number} n The index of the element to bubble up.
 */
function bubbleUp(heap, weightFunc, n) {
  var element = heap[n],
    weight = weightFunc(element);
  // When at 0, an element can not go up any further.
  while (n > 0) {
    // Compute the parent element's index, and fetch it.
    var parentN = Math.floor((n + 1) / 2) - 1,
      parent = heap[parentN];
    // If the parent has a lesser weight, things are in order and we
    // are done.
    if (weight >= weightFunc(parent)) {
      break;
    } else {
      heap[parentN] = element;
      heap[n] = parent;
      n = parentN;
    }
  }
}

/**
 * @method bubbleDown
 * @param {array} heap The heap.
 * @param {function} weightFunc The weight function.
 * @param {number} n The index of the element to sink down.
 */
function bubbleDown(heap, weightFunc, n) {
  var length = heap.length,
    node = heap[n],
    nodeWeight = weightFunc(node);

  while (true) {
    var child2N = (n + 1) * 2,
      child1N = child2N - 1;
    var swap = null;
    if (child1N < length) {
      var child1 = heap[child1N],
        child1Weight = weightFunc(child1);
      // If the score is less than our node's, we need to swap.
      if (child1Weight < nodeWeight) {
        swap = child1N;
      }
    }
    // Do the same checks for the other child.
    if (child2N < length) {
      var child2 = heap[child2N],
        child2Weight = weightFunc(child2);
      if (child2Weight < (swap === null ? nodeWeight : weightFunc(heap[child1N]))) {
        swap = child2N;
      }
    }

    if (swap === null) {
      break;
    } else {
      heap[n] = heap[swap];
      heap[swap] = node;
      n = swap;
    }
  }
}

/**
 * @class DSBinaryHeap
 * @desc DSBinaryHeap implementation of a priority queue.
 * @param {function} weightFunc Function that returns the value that should be used for node value comparison.
 * @example
 * angular.module('app').controller(function (DSBinaryHeap) {
             *      var bHeap = new DSBinaryHeap(function (x) {
             *          return x.value;
             *      });
             * );
             */
function DSBinaryHeap(weightFunc) {
  if (weightFunc && !angular.isFunction(weightFunc)) {
    throw new Error('DSBinaryHeap(weightFunc): weightFunc: must be a function!');
  }
  weightFunc = weightFunc || function (x) {
    return x;
  };
  this.weightFunc = weightFunc;
  this.heap = [];
}

/**
 * @method DSBinaryHeap.push
 * @desc Push an element into the binary heap.
 * @param {*} node The element to push into the binary heap.
 */
DSBinaryHeap.prototype.push = function (node) {
  this.heap.push(node);
  bubbleUp(this.heap, this.weightFunc, this.heap.length - 1);
};

/**
 * @method DSBinaryHeap.peek
 * @desc Return, but do not remove, the minimum element in the binary heap.
 * @returns {*}
 */
DSBinaryHeap.prototype.peek = function () {
  return this.heap[0];
};

/**
 * @method DSBinaryHeap.pop
 * @desc Remove and return the minimum element in the binary heap.
 * @returns {*}
 */
DSBinaryHeap.prototype.pop = function () {
  var front = this.heap[0],
    end = this.heap.pop();
  if (this.heap.length > 0) {
    this.heap[0] = end;
    bubbleDown(this.heap, this.weightFunc, 0);
  }
  return front;
};

/**
 * @method DSBinaryHeap.remove
 * @desc Remove the first node in the priority queue that satisfies angular.equals comparison with
 * the given node.
 * @param {*} node The node to remove.
 * @returns {*} The removed node.
 */
DSBinaryHeap.prototype.remove = function (node) {
  var length = this.heap.length;
  for (var i = 0; i < length; i++) {
    if (angular.equals(this.heap[i], node)) {
      var removed = this.heap[i],
        end = this.heap.pop();
      if (i !== length - 1) {
        this.heap[i] = end;
        bubbleUp(this.heap, this.weightFunc, i);
        bubbleDown(this.heap, this.weightFunc, i);
      }
      return removed;
    }
  }
  return null;
};

/**
 * @method DSBinaryHeap.removeAll
 * @desc Remove all nodes from this DSBinaryHeap.
 */
DSBinaryHeap.prototype.removeAll = function () {
  this.heap = [];
};

/**
 * @method DSBinaryHeap.size
 * @desc Return the size of the priority queue.
 * @returns {number} The size of the priority queue.
 */
DSBinaryHeap.prototype.size = function () {
  return this.heap.length;
};

/**
 * @desc Provider for the DSBinaryHeap.
 */
function DSBinaryHeapProvider() {
  this.$get = function () {
    return DSBinaryHeap;
  };
}

module.exports = {
  DSBinaryHeapProvider: DSBinaryHeapProvider,
  DSBinaryHeap: DSBinaryHeap
};

},{}],2:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:destroy
 * @name destroy
 * @description
 * Destroy this cache and all of its data.
 *
 * ## Signature:
 * ```js
 * DSCache#destroy()
 * ```
 *
 * ## Example:
 * ```js
 * var someCache = DSCacheFactory.get('someCache');
 *
 * someCache.destroy();
 *
 * DSCacheFactory.get('someCache'); // undefined
 * someCache.put('1', 'apple'); // Error
 * ```
 */
module.exports = function destroy() {
  var _this = this;
  clearInterval(_this.$$cacheFlushIntervalId);
  clearInterval(_this.$$recycleFreqId);
  _this.removeAll();
  if (_this.$$storage) {
    _this.$$storage.removeItem(_this.$$prefix + '.keys');
    _this.$$storage.removeItem(_this.$$prefix);
  }
  _this.$$storage = null;
  _this.$$data = null;
  _this.$$lruHeap = null;
  _this.$$expiresHeap = null;
  _this.$$prefix = null;
};

},{}],3:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:get
 * @name get
 * @description
 * Retrieve the item with the given key.
 *
 * ## Signature:
 * ```js
 * DSCache#get(key)
 * ```
 *
 * ## Examples:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 *
 * cache.get('1'); // "apple"
 * cache.get('2'); // undefined
 * ```
 *
 * ```js
 *  var options = {
 *          deleteOnExpire: 'passive',
 *          maxAge: 1000
 *      },
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  cache.get('1'); // "apple"
 *
 *  setTimeout(function () {
 *      cache.get('1'); // undefined
 *  }, 1500);
 * ```
 *
 * ```js
 *  var options = {
 *          deleteOnExpire: 'passive',
 *          maxAge: 1000
 *      },
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  cache.get('1', {
 *      onExpire: function (key, value) {
 *          console.log(key, value);
 *      }
 *  }); // "apple"
 *
 *  setTimeout(function () {
 *      cache.get('1'); // undefined
 *                      // "1" "apple" (printed to console)
 *  }, 1500);
 * ```
 *
 * ```js
 *  var options = {
 *          deleteOnExpire: 'passive',
 *          maxAge: 1000,
 *          onExpire: function (key, value, done) {
 *              console.log('global hit');
 *              if (done) {
 *                  done(key, value);
 *              }
 *          }
 *      },
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  cache.get('1', {
 *      onExpire: function (key, value) {
 *          console.log(key, value);
 *      }
 *  }); // "apple"
 *
 *  setTimeout(function () {
 *      cache.get('1'); // undefined
 *                      // "global hit" (printed to console)
 *                      // "1" "apple" (printed to console)
 *  }, 1500);
 * ```
 *
 * @param {string} key The key of the item to retrieve.
 * @param {object=} options Optional configuration. Properties:
 *
 * - `{function=}` - `onExpire` - Callback to be used if in passive `deleteOnExpire` mode and the requested item has
 * expired. If a global `onExpire` callback exists for this cache, then it will be called with three arguments: `key`,
 * `value`, and `done`, where `done` is the `onExpire` callback passed into the call to `DSCache#get(key[, options])`.
 * (See the last example above.)
 *
 * @returns {*} The item with the given key.
 */
module.exports = function get(key, options) {
  var _this = this;

  if (angular.isArray(key)) {
    var keys = key;
    var values = [];

    angular.forEach(keys, function (key) {
      var value = _this.get(key, options);
      if (value !== null && value !== undefined) {
        values.push(value);
      }
    });

    return values;
  } else {
    key = utils.stringifyNumber(key);

    if (_this.$$disabled) {
      return;
    }
  }

  options = options || {};
  if (!angular.isString(key)) {
    throw angular.$$minErr('ng')('areq', 'Expected key to be a string! Found: {0}.', typeof key);
  } else if (options && !angular.isObject(options)) {
    throw angular.$$minErr('ng')('areq', 'Expected options to be an object! Found: {0}.', typeof options);
  } else if (options.onExpire && !angular.isFunction(options.onExpire)) {
    throw angular.$$minErr('ng')('areq', 'Expected options.onExpire to be a function! Found: {0}.', typeof options.onExpire);
  }

  var item;

  if (_this.$$storage) {
    if (_this.$$promises[key]) {
      return _this.$$promises[key];
    }

    var itemJson = _this.$$storage.getItem(_this.$$prefix + '.data.' + key);

    if (itemJson) {
      item = angular.fromJson(itemJson);
    } else {
      return;
    }
  } else {
    if (!(key in _this.$$data)) {
      return;
    }

    item = _this.$$data[key];
  }

  var value = item.value;
  var now = new Date().getTime();

  if (_this.$$storage) {
    _this.$$lruHeap.remove({
      key: key,
      accessed: item.accessed
    });
    item.accessed = now;
    _this.$$lruHeap.push({
      key: key,
      accessed: now
    });
  } else {
    _this.$$lruHeap.remove(item);
    item.accessed = now;
    _this.$$lruHeap.push(item);
  }

  if (_this.$$deleteOnExpire === 'passive' && 'expires' in item && item.expires < now) {
    _this.remove(key);

    if (_this.$$onExpire) {
      _this.$$onExpire(key, item.value, options.onExpire);
    } else if (options.onExpire) {
      options.onExpire(key, item.value);
    }
    value = undefined;
  } else if (_this.$$storage) {
    _this.$$storage.setItem(_this.$$prefix + '.data.' + key, JSON.stringify(item));
  }

  return value;
};

},{"../utils":21}],4:[function(require,module,exports){
var defaults = require('../defaults');
var DSBinaryHeap = require('../DSBinaryHeap').DSBinaryHeap;

/*!
 * Configure the cache to use webStorage.
 */
function _setStorageMode(storageMode, storageImpl) {
  var _this = this;
  if (!angular.isString(storageMode)) {
    throw angular.$$minErr('ng')('areq', 'Expected storageMode to be a string! Found: {0}.', typeof storageMode);
  } else if (storageMode !== 'memory' && storageMode !== 'localStorage' && storageMode !== 'sessionStorage') {
    throw angular.$$minErr('ng')('areq', 'Expected storageMode to be "memory", "localStorage" or "sessionStorage"! Found: {0}.', storageMode);
  }

  _this.$$storageMode = storageMode;

  if (storageImpl) {
    if (!angular.isObject(storageImpl)) {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to be an object! Found: {0}.', typeof storageImpl);
    } else if (!('setItem' in storageImpl) || typeof storageImpl.setItem !== 'function') {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "setItem(key, value)"! Found: {0}.', typeof storageImpl.setItem);
    } else if (!('getItem' in storageImpl) || typeof storageImpl.getItem !== 'function') {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "getItem(key)"! Found: {0}.', typeof storageImpl.getItem);
    } else if (!('removeItem' in storageImpl) || typeof storageImpl.removeItem !== 'function') {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "removeItem(key)"! Found: {0}.', typeof storageImpl.removeItem);
    }
    _this.$$storage = storageImpl;
  } else if (_this.$$storageMode === 'localStorage') {
    try {
      localStorage.setItem('angular-cache', 'angular-cache');
      localStorage.removeItem('angular-cache');
      _this.$$storage = localStorage;
    } catch (e) {
      delete _this.$$storage;
      _this.$$storageMode = 'memory';
    }
  } else if (_this.$$storageMode === 'sessionStorage') {
    try {
      sessionStorage.setItem('angular-cache', 'angular-cache');
      sessionStorage.removeItem('angular-cache');
      _this.$$storage = sessionStorage;
    } catch (e) {
      delete _this.$$storage;
      _this.$$storageMode = 'memory';
    }
  }
}

/**
 * @doc method
 * @id DSCache.methods:setOptions
 * @name setOptions
 * @description
 * Configure this cache with the given options. With this method you can configure all of this cache's settings at once.
 *
 * ## Signature:
 * ```js
 * DSCache#setOptions(cacheOptions[, strict])
 * ```
 *
 * ## Example:
 * ```js
 *  cache.setOptions({
 *      maxAge: 60000,
 *      deleteOnExpire: 'aggressive',
 *      disabled: false
 *  });
 * ```
 *
 * @param {object} cacheOptions New configuration options for the cache. Properties:
 *
 * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
 * - `{number=}` - `maxAge` - Default: `null`
 * - `{number=}` - `deleteOnExpire` - Default: `none`
 * - `{function=}` - `onExpire` - Default: `null`
 * - `{number=}` - `cacheFlushInterval` - Default: `null`
 * - `{number=}` - `recycleFreq` - Default: `1000`
 * - `{boolean=}` - `disabled` - Default: `false`
 * - `{boolean=}` - `storeOnResolve` - If putting a promise, also put the resolved value if the promise resolves. Default: `false`.
 * - `{boolean=}` - `storeOnReject` - If putting a promise, also put the rejection value if the the promise rejects. Default: `false`.
 *
 * @param {boolean=} strict If true then any existing configuration will be reset to the defaults before
 * applying the new options, otherwise only the options specified in the options hash will be altered.
 */
function _setOptions(cacheOptions, strict) {
  var _this = this;
  cacheOptions = cacheOptions || {};
  strict = !!strict;
  if (!angular.isObject(cacheOptions)) {
    throw angular.$$minErr('ng')('areq', 'Expected cacheOptions to be an object! Found: {0}.', typeof cacheOptions);
  }

  if ('disabled' in cacheOptions) {
    _this.$$disabled = !!cacheOptions.disabled;
  } else if (strict) {
    delete _this.$$disabled;
  }

  if ('storeOnResolve' in cacheOptions) {
    _this.$$storeOnResolve = !!cacheOptions.storeOnResolve;
  } else if (strict) {
    _this.$$storeOnResolve = false;
  }

  if ('storeOnReject' in cacheOptions) {
    _this.$$storeOnReject = !!cacheOptions.storeOnReject;
  } else if (strict) {
    _this.$$storeOnReject = false;
  }

  if ('capacity' in cacheOptions) {
    _this.setCapacity(cacheOptions.capacity);
  } else if (strict) {
    _this.setCapacity(null);
  }

  if ('deleteOnExpire' in cacheOptions) {
    _this.setDeleteOnExpire(cacheOptions.deleteOnExpire);
  } else if (strict) {
    _this.setDeleteOnExpire(null);
  }

  if ('maxAge' in cacheOptions) {
    _this.setMaxAge(cacheOptions.maxAge);
  } else if (strict) {
    _this.setMaxAge(null);
  }

  if ('recycleFreq' in cacheOptions) {
    _this.setRecycleFreq(cacheOptions.recycleFreq);
  } else if (strict) {
    _this.setRecycleFreq(null);
  }

  if ('cacheFlushInterval' in cacheOptions) {
    _this.setCacheFlushInterval(cacheOptions.cacheFlushInterval);
  } else if (strict) {
    _this.setCacheFlushInterval(null);
  }

  if ('onExpire' in cacheOptions) {
    _this.setOnExpire(cacheOptions.onExpire);
  } else if (strict) {
    _this.setOnExpire(null);
  }
}

/**
 * @doc function
 * @id DSCache
 * @name DSCache
 * @description
 * Instantiated via `DSCacheFactory(cacheId[, options])`.
 *
 * @param {string} cacheId The id of the new cache.
 * @param {object=} options Configuration options.
 */
function DSCache(cacheId, options) {
  var _this = this;

  _this.$$data = {};
  _this.$$promises = {};
  _this.$$id = cacheId;
  _this.$$storage = null;

  _this.$$expiresHeap = new DSBinaryHeap(function (x) {
    return x.expires;
  });

  _this.$$lruHeap = new DSBinaryHeap(function (x) {
    return x.accessed;
  });

  options = options || {};

  if ('storageMode' in options) {
    _setStorageMode.apply(_this, [options.storageMode, options.storageImpl]);
  }
  if ('storagePrefix' in options) {
    _this.$$storagePrefix = options.storagePrefix;
  }

  _this.$$prefix = _this.$$storagePrefix + cacheId;

  // Initialize _this cache with the default and given options
  _setOptions.apply(_this, [options, true]);
}

for (var key in defaults.defaults) {
  DSCache.prototype['$$' + key] = defaults.defaults[key];
}

/**
 * @doc method
 * @id DSCache.methods:setOptions
 * @name setOptions
 * @methodOf DSCache
 * @description
 * See [DSCache.setOptions](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setOptions = _setOptions;

/**
 * @doc method
 * @id DSCache.methods:setCapacity
 * @name setCapacity
 * @methodOf DSCache
 * @description
 * See [DSCache.setCapacity](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setCapacity = require('./setCapacity');

/**
 * @doc method
 * @id DSCache.methods:setDeleteOnExpire
 * @name setDeleteOnExpire
 * @methodOf DSCache
 * @description
 * See [DSCache.setDeleteOnExpire](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setDeleteOnExpire = require('./setDeleteOnExpire');

/**
 * @doc method
 * @id DSCache.methods:setMaxAge
 * @name setMaxAge
 * @methodOf DSCache
 * @description
 * See [DSCache.setMaxAge](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setMaxAge = require('./setMaxAge');

/**
 * @doc method
 * @id DSCache.methods:setRecycleFreq
 * @name setRecycleFreq
 * @methodOf DSCache
 * @description
 * See [DSCache.setRecycleFreq](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setRecycleFreq = require('./setRecycleFreq');

/**
 * @doc method
 * @id DSCache.methods:setCacheFlushInterval
 * @name setCacheFlushInterval
 * @methodOf DSCache
 * @description
 * See [DSCache.setCacheFlushInterval](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setCacheFlushInterval = require('./setCacheFlushInterval');

/**
 * @doc method
 * @id DSCache.methods:setOnExpire
 * @name setOnExpire
 * @methodOf DSCache
 * @description
 * See [DSCache.setOnExpire](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setOnExpire = require('./setOnExpire');

/**
 * @doc method
 * @id DSCache.methods:put
 * @name put
 * @methodOf DSCache
 * @description
 * See [DSCache.put](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.put = require('./put');

/**
 * @doc method
 * @id DSCache.methods:get
 * @name get
 * @methodOf DSCache
 * @description
 * See [DSCache.get](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.get = require('./get');

/**
 * @doc method
 * @id DSCache.methods:remove
 * @name remove
 * @methodOf DSCache
 * @description
 * See [DSCache.remove](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.remove = require('./remove');

/**
 * @doc method
 * @id DSCache.methods:removeAll
 * @name removeAll
 * @methodOf DSCache
 * @description
 * See [DSCache.removeAll](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.removeAll = require('./removeAll');

/**
 * @doc method
 * @id DSCache.methods:removeExpired
 * @name removeExpired
 * @methodOf DSCache
 * @description
 * See [DSCache.removeExpired](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.removeExpired = require('./removeExpired');

/**
 * @doc method
 * @id DSCache.methods:destroy
 * @name destroy
 * @methodOf DSCache
 * @description
 * See [DSCache.destroy](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.destroy = require('./destroy');

/**
 * @doc method
 * @id DSCache.methods:info
 * @name info
 * @methodOf DSCache
 * @description
 * See [DSCache.info](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.info = require('./info');

/**
 * @doc method
 * @id DSCache.methods:keySet
 * @name keySet
 * @methodOf DSCache
 * @description
 * See [DSCache.keySet](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.keySet = require('./keySet');

/**
 * @doc method
 * @id DSCache.methods:keys
 * @name keys
 * @methodOf DSCache
 * @description
 * See [DSCache.keys](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.keys = require('./keys');

/**
 * @doc method
 * @id DSCache.methods:disable
 * @name disable
 * @description
 * Disable this cache. Disabling a cache does not remove any data, it just turns DSCache#get and DSCache#put into noops.
 *
 * ## Signature:
 * ```js
 * DSCache#disable()
 * ```
 *
 * ## Example:
 * ```js
 *  var cache = DSCacheFactory.get('cache');
 *
 *  cache.put('1', 'apple');
 *  cache.get('1'); // "apple"
 *  cache.info().size; // 1
 *
 *  cache.disable();
 *  cache.info().size; // 1
 *
 *  cache.get('1'); // undefined
 *  cache.put('2', 'banana'); // undefined
 *  cache.get('2'); // undefined
 *  cache.info().size; // 1
 * ```
 */
DSCache.prototype.disable = function () {
  this.$$disabled = true;
};

/**
 * @doc method
 * @id DSCache.methods:enable
 * @name enable
 * @description
 * Enable this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#enable()
 * ```
 *
 * ## Example:
 * ```js
 *  var options = {
 *      disabled: true
 *  };
 *  var cache = DSCacheFactory.get('cache', options);
 *
 *  cache.put('1', 'apple');
 *  cache.get('1'); // undefined
 *
 *  cache.enable();
 *
 *  cache.put('1', 'apple');
 *  cache.get('1'); // "apple"
 * ```
 */
DSCache.prototype.enable = function () {
  delete this.$$disabled;
};

/**
 * @doc method
 * @id DSCache.methods:touch
 * @name touch
 * @description
 * Reset the expiry of a single item or all items in the cache.
 *
 * ## Signature:
 * ```js
 * DSCache#touch(key)
 * ```
 *
 * ## Example:
 * ```js
 *  cache.touch('1'); // touch one item
 *
 *  cache.touch(); // touch all items
 * ```
 *
 * @param {string=} key The key of the item to touch.
 */
DSCache.prototype.touch = function (key) {
  var _this = this;
  if (key) {
    var val = _this.get(key, {
      onExpire: function (k, v) {
        _this.put(k, v);
      }
    });
    if (val) {
      _this.put(key, val);
    }
  } else {
    var keys = _this.keys();
    for (var i = 0; i < keys.length; i++) {
      _this.touch(keys[i]);
    }
  }
};

module.exports = DSCache;

},{"../DSBinaryHeap":1,"../defaults":19,"./destroy":2,"./get":3,"./info":5,"./keySet":6,"./keys":7,"./put":8,"./remove":9,"./removeAll":10,"./removeExpired":11,"./setCacheFlushInterval":12,"./setCapacity":13,"./setDeleteOnExpire":14,"./setMaxAge":15,"./setOnExpire":16,"./setRecycleFreq":17}],5:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:info
 * @name info
 * @description
 * Return the status of this cache, or if `key` is provided return the status of the item with that key.
 *
 * ## Signature:
 * ```js
 * DSCache#info([key])
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 *
 * cache.info();    //  {
 *                  //      id: 'cache',
 *                  //      capacity: Number.MAX_VALUE,
 *                  //      maxAge: Number.MAX_VALUE,
 *                  //      deleteOnExpire: 'none',
 *                  //      onExpire: null,
 *                  //      cacheFlushInterval: null,
 *                  //      recycleFreq: 1000,
 *                  //      storageMode: 'memory',
 *                  //      storageImpl: null,
 *                  //      disabled: false,
 *                  //      size: 2
 *                  //  }
 *
 * cache.info('1'); //  {
 *                  //      created: 1234567890,
 *                  //      accessed: 1234567890,
 *                  //      expires: Number.MAX_VALUE,
 *                  //      isExpired: false
 *                  //  }
 *
 * cache.info('3'); // undefined
 * ```
 *
 * @param {string=} key The key of the item whose status is to be retrieved.
 * @returns {object} The status of this cache or of the item with the given key.
 */
module.exports = function info(key) {
  var _this = this;
  if (key) {
    var item;
    if (_this.$$storage) {
      var itemJson = _this.$$storage.getItem(_this.$$prefix + '.data.' + key);

      if (itemJson) {
        item = angular.fromJson(itemJson);
        return {
          created: item.created,
          accessed: item.accessed,
          expires: item.expires,
          isExpired: (new Date().getTime() - item.created) > _this.$$maxAge
        };
      } else {
        return undefined;
      }
    } else {
      if (key in _this.$$data) {
        item = _this.$$data[key];

        return {
          created: item.created,
          accessed: item.accessed,
          expires: item.expires,
          isExpired: (new Date().getTime() - item.created) > _this.$$maxAge
        };
      } else {
        return undefined;
      }
    }
  } else {
    return {
      id: _this.$$id,
      capacity: _this.$$capacity,
      maxAge: _this.$$maxAge,
      deleteOnExpire: _this.$$deleteOnExpire,
      onExpire: _this.$$onExpire,
      cacheFlushInterval: _this.$$cacheFlushInterval,
      recycleFreq: _this.$$recycleFreq,
      storageMode: _this.$$storageMode,
      storageImpl: _this.$$storage,
      disabled: _this.$$disabled,
      size: _this.$$lruHeap && _this.$$lruHeap.size() || 0
    };
  }
};

},{}],6:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:keySet
 * @name keySet
 * @description
 * Return an object of the keys in this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#keySet()
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 *
 * cache.keys(); // { "1": "1", "2": "2" }
 * ```
 *
 * @returns {object} An object of the keys in this cache.
 */
module.exports = function keySet() {
  var _this = this;
  if (_this.$$storage) {
    var keysJson = _this.$$storage.getItem(_this.$$prefix + '.keys'),
      kSet = {};

    if (keysJson) {
      var keys = angular.fromJson(keysJson);

      for (var i = 0; i < keys.length; i++) {
        kSet[keys[i]] = keys[i];
      }
    }
    return kSet;
  } else {
    return utils.keySet(_this.$$data);
  }
};

},{"../utils":21}],7:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:keys
 * @name keys
 * @description
 * Return an array of the keys in this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#keys()
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 *
 * cache.keys(); // [ "1", "2" ]
 * ```
 *
 * @returns {Array} An array of the keys in this cache.
 */
module.exports = function keys() {
  var _this = this;
  if (_this.$$storage) {
    var keysJson = _this.$$storage.getItem(_this.$$prefix + '.keys');

    if (keysJson) {
      return angular.fromJson(keysJson);
    } else {
      return [];
    }
  } else {
    return utils.keys(_this.$$data);
  }
};

},{"../utils":21}],8:[function(require,module,exports){
var utils = require('../utils');

function isPromiseLike(v) {
  return v && typeof v.then === 'function';
}

/**
 * @doc method
 * @id DSCache.methods:put
 * @name put
 * @description
 * Insert a value into the cache under the given key.
 *
 * ## Signature:
 * ```js
 * DSCache#put(key, value)
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 3);
 * cache.put('3', { stuff: 'more stuff' });
 *
 * cache.get('1'); // "apple"
 * cache.get('2'); // 3
 * cache.get('3'); // { stuff: 'more stuff' }
 * cache.get('4'); // undefined
 * ```
 *
 * ## Throws:
 * - `Error` - `key` must be a string.
 *
 * @param {string} key The key under which to store the given value.
 * @param {*} value The value to store.
 * @param {options=} options Configuration options. Properties:
 *
 *  - `{boolean=}` - `storeOnResolve` - If putting a promise, put the resolved value if the promise resolves.
 *  - `{boolean=}` - `storeOnReject` - If putting a promise, put the rejection value if the the promise rejects.
 *
 * @returns {*} The newly stored item.
 */
module.exports = function put(key, value, options) {
  options = options || {};

  var _this = this;
  var storeOnResolve = 'storeOnResolve' in options ? !!options.storeOnResolve : _this.$$storeOnResolve;
  var storeOnReject = 'storeOnReject' in options ? !!options.storeOnReject : _this.$$storeOnReject;

  function getHandler(store, isError) {
    return function handlePromise(v) {
      if (store) {
        delete _this.$$promises[key];
        if (angular.isObject(v) && 'status' in v && 'data' in v) {
          v = [v.status, v.data, v.headers(), v.statusText];
          _this.put(key, v);
        } else {
          _this.put(key, v);
        }
      }
      if (isError) {
        return _this.$q.reject(v);
      } else {
        return v;
      }
    };
  }

  if (_this.$$disabled || value === null || value === undefined) {
    return;
  }
  key = utils.stringifyNumber(key);

  if (!angular.isString(key)) {
    throw angular.$$minErr('ng')('areq', 'Expected key to be a string! Found: {0}.', typeof key);
  }

  var now = new Date().getTime();
  var item = {
    key: key,
    value: isPromiseLike(value) ? value.then(getHandler(storeOnResolve, false), getHandler(storeOnReject, true)) : value,
    created: now,
    accessed: now
  };

  item.expires = item.created + _this.$$maxAge;

  if (_this.$$storage) {
    if (isPromiseLike(item.value)) {
      _this.$$promises[key] = item.value;
      return _this.$$promises[key];
    }
    var keysJson = _this.$$storage.getItem(_this.$$prefix + '.keys');
    var keys = keysJson ? angular.fromJson(keysJson) : [];
    var itemJson = _this.$$storage.getItem(_this.$$prefix + '.data.' + key);

    // Remove existing
    if (itemJson) {
      _this.remove(key);
    }
    // Add to expires heap
    _this.$$expiresHeap.push({
      key: key,
      expires: item.expires
    });
    // Add to lru heap
    _this.$$lruHeap.push({
      key: key,
      accessed: item.accessed
    });
    // Set item
    _this.$$storage.setItem(_this.$$prefix + '.data.' + key, JSON.stringify(item));
    var exists = false;
    for (var i = 0; i < keys.length; i++) {
      if (keys[i] === key) {
        exists = true;
        break;
      }
    }
    if (!exists) {
      keys.push(key);
    }
    _this.$$storage.setItem(_this.$$prefix + '.keys', JSON.stringify(keys));
  } else {
    // Remove existing
    if (_this.$$data[key]) {
      _this.remove(key);
    }
    // Add to expires heap
    _this.$$expiresHeap.push(item);
    // Add to lru heap
    _this.$$lruHeap.push(item);
    // Set item
    _this.$$data[key] = item;
    delete _this.$$promises[key];
  }

  // Handle exceeded capacity
  if (_this.$$lruHeap.size() > _this.$$capacity) {
    _this.remove(_this.$$lruHeap.peek().key);
  }

  return value;
};

},{"../utils":21}],9:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:remove
 * @name remove
 * @description
 * Remove the item with the given key.
 *
 * ## Signature:
 * ```js
 * DSCache#remove(key)
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 *
 * cache.get('1'); // "apple"
 *
 * cache.remove('1'); // "apple"
 *
 * cache.get('1'); // undefined
 * ```
 *
 * @param {string} key The key of the item to remove.
 * @returns {*} The removed item if an item was removed.
 */
module.exports = function remove(key) {
  var _this = this;
  delete _this.$$promises[key];
  if (_this.$$storage) {
    var itemJson = _this.$$storage.getItem(_this.$$prefix + '.data.' + key);

    if (itemJson) {
      var item = angular.fromJson(itemJson);
      _this.$$lruHeap.remove({
        key: key,
        accessed: item.accessed
      });
      _this.$$expiresHeap.remove({
        key: key,
        expires: item.expires
      });
      _this.$$storage.removeItem(_this.$$prefix + '.data.' + key);
      var keysJson = _this.$$storage.getItem(_this.$$prefix + '.keys'),
        keys = keysJson ? angular.fromJson(keysJson) : [],
        index = keys.indexOf(key);

      if (index >= 0) {
        keys.splice(index, 1);
      }
      _this.$$storage.setItem(_this.$$prefix + '.keys', JSON.stringify(keys));
      return item.value;
    }
  } else {
    var value = _this.$$data[key] ? _this.$$data[key].value : undefined;
    _this.$$lruHeap.remove(_this.$$data[key]);
    _this.$$expiresHeap.remove(_this.$$data[key]);
    _this.$$data[key] = null;
    delete _this.$$data[key];
    return value;
  }
};

},{}],10:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:removeAll
 * @name removeAll
 * @description
 * Remove all items from this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#removeAll()
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 * cache.info().size; // 2
 *
 * cache.get('1'); // "apple"
 * cache.get('2'); // "banana"
 *
 * cache.removeAll();
 * cache.info().size; // 0
 *
 * cache.get('1'); // undefined
 * cache.get('2'); // undefined
 * ```
 */
module.exports = function removeAll() {
  var _this = this;
  if (_this.$$storage) {
    _this.$$lruHeap.removeAll();
    _this.$$expiresHeap.removeAll();
    var keysJson = _this.$$storage.getItem(_this.$$prefix + '.keys');

    if (keysJson) {
      var keys = angular.fromJson(keysJson);

      for (var i = 0; i < keys.length; i++) {
        _this.remove(keys[i]);
      }
    }
    _this.$$storage.setItem(_this.$$prefix + '.keys', JSON.stringify([]));
  } else {
    _this.$$lruHeap.removeAll();
    _this.$$expiresHeap.removeAll();
    for (var key in _this.$$data) {
      _this.$$data[key] = null;
    }
    _this.$$data = {};
  }
};

},{}],11:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:removeExpired
 * @name removeExpired
 * @description
 * Remove and return all expired items from the cache.
 *
 * ## Signature:
 * ```js
 * DSCache#removeExpired()
 * ```
 *
 * ## Example:
 * ```js
 *  var options = {
 *          maxAge: 1000
 *      },
 *      // deleteOnExpire defaults to "none"
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *  cache.put('2', 'banana');
 *
 *  setTimeout(function () {
 *      cache.put('3', 'orange');
 *
 *      cache.info().size; // 3
 *      cache.info('1').isExpired; // true
 *      cache.info('2').isExpired; // true
 *      cache.info('3').isExpired; // false
 *
 *      cache.removeExpired(); // { "1": "apple", "2": "banana" }
 *
 *      cache.info().size; // 1
 *      cache.get('1'); // undefined
 *      cache.get('2'); // undefined
 *      cache.info('3').isExpired; // false
 *  }, 1500);
 * ```
 *
 * @returns {object} The removed items, if any.
 */
module.exports = function removeExpired() {
  var _this = this;
  var now = new Date().getTime();
  var expired = {};
  var key;
  var expiredItem;

  while ((expiredItem = _this.$$expiresHeap.peek()) && expiredItem.expires < now) {
    expired[expiredItem.key] = expiredItem.value ? expiredItem.value : null;
    _this.$$expiresHeap.pop();
  }

  if (_this.$$storage) {
    for (key in expired) {
      var itemJson = _this.$$storage.getItem(_this.$$prefix + '.data.' + key);
      if (itemJson) {
        expired[key] = angular.fromJson(itemJson).value;
        _this.remove(key);
      }
    }
  } else {
    for (key in expired) {
      _this.remove(key);
    }
  }

  if (_this.$$onExpire) {
    for (key in expired) {
      _this.$$onExpire(key, expired[key]);
    }
  }

  return expired;
};

},{}],12:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setCacheFlushInterval
 * @name setCacheFlushInterval
 * @description
 * Set the `cacheFlushInterval` setting for this cache. If set, this setting will cause this cache to periodically
 * clear itself.
 *
 * ## Signature:
 * ```js
 * DSCache#setCacheFlushInterval(cacheFlushInterval)
 * ```
 *
 * ## Example:
 * ```js
 *  var cache = DSCacheFactory('cache');
 *
 *  cache.put('1', 'apple');
 *  cache.put('2', 'banana');
 *
 *  cache.info().size; // 2
 *  cache.setCacheFlushInterval(60000);
 *
 *  setTimeout(function () {
 *      cache.info().size; // 0
 *  }, 90000);
 * ```
 *
 * ## Throws:
 * - `Error` - `cacheFlushInterval` must be `null` or a number greater than zero.
 *
 * @param {number|null} cacheFlushInterval The new cacheFlushInterval for this cache in milliseconds. If
 * `cacheFlushInterval` is `null` then `cacheFlushInterval` for this cache will be reset to the default (`null`).
 */
module.exports = function setCacheFlushInterval(cacheFlushInterval) {
  var _this = this;
  if (cacheFlushInterval === null) {
    delete _this.$$cacheFlushInterval;
  } else if (!angular.isNumber(cacheFlushInterval)) {
    throw angular.$$minErr('ng')('areq', 'Expected cacheFlushInterval to be a number! Found: {0}.', typeof cacheFlushInterval);
  } else if (cacheFlushInterval < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected cacheFlushInterval to be greater than zero! Found: {0}.', cacheFlushInterval);
  } else if (cacheFlushInterval !== _this.$$cacheFlushInterval) {
    _this.$$cacheFlushInterval = cacheFlushInterval;
    clearInterval(_this.$$cacheFlushIntervalId);
    (function (self) {
      self.$$cacheFlushIntervalId = setInterval(function () {
        self.removeAll();
      }, self.$$cacheFlushInterval);
    })(_this);
  }
};

},{}],13:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setCapacity
 * @name setCapacity
 * @description
 * Set the capacity for this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#setCapacity(capacity)
 * ```
 *
 * ## Example:
 * ```js
 * var smallCache = DSCacheFactory('smallCache', { capacity: 2 });
 *
 * smallCache.info().size; // 0
 *
 * smallCache.put('1', 'apple');
 * smallCache.put('2', 'banana');
 *
 * smallCache.info().size; // 2
 *
 * // Least-recently used items are removed
 * // when the cache's new capacity exceeds
 * // its size
 * smallCache.setCapacity(1);
 *
 * smallCache.get('1'); // undefined
 * smallCache.info().size; // 1
 * ```
 *
 * ## Throws:
 * - `Error` - `capacity` must be `null` or a number greater than zero.
 *
 * @param {number|null} capacity The new capacity for this cache. If `capacity` is `null` then the capacity for this cache
 * will be reset to the default (`Number.MAX_VALUE`).
 * @returns {object} Key-value pairs of any items removed because this cache's size exceeds the new capacity.
 */
module.exports = function setCapacity(capacity) {
  var _this = this;
  if (capacity === null) {
    delete _this.$$capacity;
  } else if (!angular.isNumber(capacity)) {
    throw angular.$$minErr('ng')('areq', 'Expected capacity to be a number! Found: {0}.', typeof capacity);
  } else if (capacity < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected capacity to be greater than zero! Found: {0}.', capacity);
  } else {
    _this.$$capacity = capacity;
  }
  var removed = {};
  while (_this.$$lruHeap.size() > _this.$$capacity) {
    removed[_this.$$lruHeap.peek().key] = _this.remove(_this.$$lruHeap.peek().key);
  }
  return removed;
};

},{}],14:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setDeleteOnExpire
 * @name setDeleteOnExpire
 * @description
 * Set the behavior for this cache for when items expire. This setting determines what this cache will do when one of
 * its items expires.
 *
 * ## Possible Values:
 * - `"none"` - Do nothing when items expire.
 * - `"passive"` - Do nothing when items expire, but if an expired item is requested, remove it from the cache and return `undefined`.
 * - `"aggressive"` - Scan for expired items on the interval specified by the `recycleFreq` setting for this cache (defaults
 * to `1000ms`) and actively remove any expired items.
 *
 * ## Signature:
 * ```js
 * DSCache#setDeleteOnExpire(deleteOnExpire)
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 *
 * // Wait a few seconds
 *
 * cache.get('1'); // "apple"
 *
 * cache.setDeleteOnExpire('aggressive');
 *
 * // Wait a few seconds
 *
 * cache.get('1'); // undefined
 * ```
 *
 * ## Throws:
 * - `Error` - `deleteOnExpire` must be `null`, `"none"`, `"passive"` or `"aggressive"`.
 *
 * @param {string|null} deleteOnExpire The new deleteOnExpire for this cache. If `deleteOnExpire` is `null` then
 * `deleteOnExpire` for this cache will be reset to the default (`"none"`).
 */
module.exports = function setDeleteOnExpire(deleteOnExpire) {
  var _this = this;
  if (deleteOnExpire === null) {
    delete _this.$$deleteOnExpire;
  } else if (!angular.isString(deleteOnExpire)) {
    throw angular.$$minErr('ng')('areq', 'Expected deleteOnExpire to be a string! Found: {0}.', typeof deleteOnExpire);
  } else if (deleteOnExpire !== 'none' && deleteOnExpire !== 'passive' && deleteOnExpire !== 'aggressive') {
    throw angular.$$minErr('ng')('areq', 'Expected deleteOnExpire to be "none", "passive" or "aggressive"! Found: {0}.', deleteOnExpire);
  } else {
    _this.$$deleteOnExpire = deleteOnExpire;
  }
  _this.setRecycleFreq(_this.$$recycleFreq);
};

},{}],15:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:setMaxAge
 * @name setMaxAge
 * @description
 * Set the `maxAge` setting for this cache. This setting specifies how long items can be in the cache before they expire.
 *
 * ## Signature:
 * ```js
 * DSCache#setMaxAge(maxAge)
 * ```
 *
 * ## Example:
 * ```js
 *  var cache = DSCacheFactory('cache', { deleteOnExpire: 'aggressive' });
 *
 *  // This won't expire for a long time
 *  cache.put('1', 'apple');
 *
 *  setTimeout(function () {
 *      // 'apple' will be removed because it
 *      // has already been in the cache longer
 *      // than the new maxAge
 *      var removed = cache.setMaxAge(1000);
 *
 *      removed; // {
 *               //     '1': 'apple'
 *               // }
 *  }, 1500);
 * ```
 *
 * ## Throws:
 * - `Error` - `maxAge must be `null` or a number greater than zero.
 *
 * @param {number} maxAge The new maxAge for this cache in milliseconds. If `maxAge` is `null` then `maxAge` for this
 * cache will be reset to the default (`Number.MAX_VALUE`);
 * @returns {object} Key-value pairs of any items aggressively removed because they are expired according to the new
 * `maxAge`. Items are only removed if the `deleteOnExpire` setting for this cache is set to `"aggressive"`.
 */
module.exports = function setMaxAge(maxAge) {
  var _this = this;
  if (maxAge === null) {
    delete _this.$$maxAge;
  } else if (!angular.isNumber(maxAge)) {
    throw angular.$$minErr('ng')('areq', 'Expected maxAge to be a number! Found: {0}.', typeof maxAge);
  } else if (maxAge < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected maxAge to be greater than zero! Found: {0}.', maxAge);
  } else {
    _this.$$maxAge = maxAge;
  }
  var i, keys, key;

  _this.$$expiresHeap.removeAll();

  if (_this.$$storage) {
    var keysJson = _this.$$storage.getItem(_this.$$prefix + '.keys');

    keys = keysJson ? angular.fromJson(keysJson) : [];

    for (i = 0; i < keys.length; i++) {
      key = keys[i];
      var itemJson = _this.$$storage.getItem(_this.$$prefix + '.data.' + key);

      if (itemJson) {
        var item = angular.fromJson(itemJson);
        if (_this.$$maxAge === Number.MAX_VALUE) {
          item.expires = Number.MAX_VALUE;
        } else {
          item.expires = item.created + _this.$$maxAge;
        }
        _this.$$expiresHeap.push({
          key: key,
          expires: item.expires
        });
      }
    }
  } else {
    keys = utils.keys(_this.$$data);

    for (i = 0; i < keys.length; i++) {
      key = keys[i];
      if (_this.$$maxAge === Number.MAX_VALUE) {
        _this.$$data[key].expires = Number.MAX_VALUE;
      } else {
        _this.$$data[key].expires = _this.$$data[key].created + _this.$$maxAge;
      }
      _this.$$expiresHeap.push(_this.$$data[key]);
    }
  }
  if (_this.$$deleteOnExpire === 'aggressive') {
    return _this.removeExpired();
  } else {
    return {};
  }
};

},{"../utils":21}],16:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setOnExpire
 * @name setOnExpire
 * @description
 * Set the global `onExpire` callback for this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#setOnExpire(onExpire)
 * ```
 *
 * ## Examples:
 * ```js
 *  var options = {
 *      onExpire: function (key, value) {
 *          window.lastExpiredItem = key;
 *      },
 *      maxAge: 1000,
 *      deleteOnExpire: 'aggressive'
 *  };
 *  var cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  setTimeout(function () {
 *      window.lastExpiredItem; // '1'
 *  }, 1500);
 * ```
 *
 * ## Throws:
 * - `Error` - `cacheFlushInterval` must be `null` or a number greater than zero.
 *
 * @param {function|null} onExpire The new onExpire callback for this cache. If `onExpire` is `null` then the onExpire
 * callback for this cache will be removed.
 */
module.exports = function setOnExpire(onExpire) {
  if (onExpire === null) {
    delete this.$$onExpire;
  } else if (!angular.isFunction(onExpire)) {
    throw angular.$$minErr('ng')('areq', 'Expected onExpire to be a function! Found: {0}.', typeof onExpire);
  } else {
    this.$$onExpire = onExpire;
  }
};

},{}],17:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setRecycleFreq
 * @name setRecycleFreq
 * @description
 * Set the `recycleFreq` setting for this cache. This setting determines how often this cache will scan for expired
 * items. The cache will only scan for expired items if the `deleteOnExpire` setting for this cache is set to
 * `"aggressive"`.
 *
 * ## Signature:
 * ```js
 * DSCache#setRecycleFreq(recycleFreq)
 * ```
 *
 * ## Example:
 * ```js
 *  var options = {
 *      deleteOnExpire: 'aggressive',
 *      maxAge: 1000
 *  };
 *  var cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  setTimeout(function () {
 *
 *      cache.get('1'); // undefined
 *      cache.setRecycleFreq(60000);
 *
 *      // This expires after 1 second, but the cache
 *      // only checks every 60 seconds now
 *      cache.put('1', 'apple');
 *
 *      setTimeout(function () {
 *          // expired, but won't be removed
 *          // until the next check
 *          cache.get('1'); // "apple"
 *          cache.info('1').isExpired; // true
 *      }, 1500);
 *  }, 1500);
 * ```
 *
 * ## Throws:
 * - `Error` - `recycleFreq` must be `null` or a number greater than zero.
 *
 * @param {number} recycleFreq The new recycleFreq for this cache in milliseconds. If `recycleFreq` is `null` then
 * `recycleFreq` for this cache will be reset to the default (`1000` milliseconds).
 */
module.exports = function setRecycleFreq(recycleFreq) {
  var _this = this;
  if (recycleFreq === null) {
    delete _this.$$recycleFreq;
  } else if (!angular.isNumber(recycleFreq)) {
    throw angular.$$minErr('ng')('areq', 'Expected recycleFreq to be a number! Found: {0}.', typeof recycleFreq);
  } else if (recycleFreq < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected recycleFreq to be greater than zero! Found: {0}.', recycleFreq);
  } else {
    _this.$$recycleFreq = recycleFreq;
  }
  clearInterval(_this.$$recycleFreqId);
  if (_this.$$deleteOnExpire === 'aggressive') {
    (function (self) {
      self.$$recycleFreqId = setInterval(function () {
        self.removeExpired();
      }, self.$$recycleFreq);
    })(_this);
  } else {
    delete _this.$$recycleFreqId;
  }
};

},{}],18:[function(require,module,exports){
var defaults = require('../defaults');
var DSCache = require('../DSCache');
var version = '3.2.2';

/**
 * @doc function
 * @id DSCacheFactoryProvider
 * @name DSCacheFactoryProvider
 */
function DSCacheFactoryProvider() {

  var _this = this;

  var config = new defaults.Config();

  _this.version = version;

  /**
   * @doc method
   * @id DSCacheFactoryProvider.methods:setCacheDefaults
   * @name setCacheDefaults
   * @desc Set the default configuration for all caches created by $angularCacheFactory.
   * @param {object} options Default configuration options for each new cache.
   */
  _this.setCacheDefaults = function (options) {
    options = options || {};

    if (!angular.isObject(options)) {
      throw angular.$$minErr('ng')('areq', 'Expected options to be an object! Found: {0}.', typeof options);
    }

    for (var key in defaults.defaults) {
      if (key in options) {
        config[key] = options[key];
      }
    }
    if ('disabled' in options) {
      config.$$disabled = !!options.disabled;
    }
  };

  _this.$get = ['$q', function ($q) {
    var caches = {};

    /*!
     * @method _keys
     * @desc Returns an array of the keys of the given collection.
     * @param {object} collection The collection from which to get the keys.
     * @returns {array} An array of the keys of the given collection.
     */
    function _keys(collection) {
      var keys = [], key;
      for (key in collection) {
        if (collection.hasOwnProperty(key)) {
          keys.push(key);
        }
      }
      return keys;
    }

    function createCache(cacheId, options) {
      if (cacheId in caches) {
        throw angular.$$minErr('$cacheFactory')('iid', "CacheId '{0}' is already taken!", cacheId);
      } else if (!angular.isString(cacheId)) {
        throw angular.$$minErr('ng')('areq', 'Expected cacheId to be a string! Found: {0}.', typeof cacheId);
      }

      caches[cacheId] = new DSCache(cacheId, angular.extend({}, config, options));
      caches[cacheId].destroy = function () {
        this.constructor.prototype.destroy.call(this);
        delete caches[this.$$id];
      };
      caches[cacheId].$q = $q;
      return caches[cacheId];
    }

    /**
     * @doc function
     * @id DSCacheFactory
     * @name DSCacheFactory
     * @description
     * Factory function that produces instances of `DSCache`.
     *
     * @param {string} cacheId The id of the new cache.
     * @param {object} options Configuration options. Properties:
     *
     * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
     * - `{number=}` - `maxAge` - Default: `null`
     * - `{number=}` - `deleteOnExpire` - Default: `none`
     * - `{function=}` - `onExpire` - Default: `null`
     * - `{number=}` - `cacheFlushInterval` - Default: `null`
     * - `{number=}` - `recycleFreq` - Default: `1000`
     * - `{number=}` - `deleteOnExpire` - Default: `null`
     * - `{string=}` - `storageMode` - Default: `'none`
     * - `{object=}` - `storageImpl` - Default: `null`
     * - `{boolean=}` - `disabled` - Default: `false`
     * - `{string=}` - `storagePrefix` - Default: `"angular-cache.caches."`
     *
     * @returns {DSCache} New instance of DSCache.
     */
    function DSCacheFactory(cacheId, options) {
      return createCache(cacheId, options);
    }

    /**
     * @doc method
     * @id DSCacheFactory.methods:createCache
     * @name createCache
     * @description
     * Factory function that produces instances of `DSCache`.
     *
     * @param {string} cacheId The id of the new cache.
     * @param {object} options Configuration options. Properties:
     *
     * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
     * - `{number=}` - `maxAge` - Default: `null`
     * - `{number=}` - `deleteOnExpire` - Default: `none`
     * - `{function=}` - `onExpire` - Default: `null`
     * - `{number=}` - `cacheFlushInterval` - Default: `null`
     * - `{number=}` - `recycleFreq` - Default: `1000`
     * - `{number=}` - `deleteOnExpire` - Default: `null`
     * - `{string=}` - `storageMode` - Default: `'none`
     * - `{object=}` - `storageImpl` - Default: `null`
     * - `{boolean=}` - `disabled` - Default: `false`
     * - `{string=}` - `storagePrefix` - Default: `"angular-cache.caches."`
     *
     * @returns {DSCache} New instance of DSCache.
     */
    DSCacheFactory.createCache = createCache;

    DSCacheFactory.version = version;

    /**
     * @doc method
     * @id DSCacheFactory.methods:info
     * @name info
     * @description
     * Return the status of `DSCacheFactory`.
     * @returns {object} The status of `DSCacheFactory`.
     */
    DSCacheFactory.info = function () {
      var keys = _keys(caches);
      var info = {
        size: keys.length,
        caches: {}
      };
      for (var i = 0; i < keys.length; i++) {
        var key = keys[i];
        info.caches[key] = caches[key].info();
      }
      var c = info.cacheDefaults = angular.extend({}, config);
      for (var option in defaults.defaults) {
        if (!(option in c)) {
          c[option] = config['$$' + option];
        }
      }
      return info;
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:get
     * @name get
     * @description
     * Return the cache with the given `cacheId`.
     * @param {string} cacheId The id of the desired cache.
     * @returns {DSCache} The cache with the specified `cacheId`.
     */
    DSCacheFactory.get = function (cacheId) {
      if (!angular.isString(cacheId)) {
        throw angular.$$minErr('ng')('areq', 'Expected cacheId to be a string! Found: {0}.', typeof cacheId);
      }
      return caches[cacheId];
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:keySet
     * @name keySet
     * @description
     * Return an object containing the `cacheId` of each cache.
     * @returns {object} An object containing the `cacheId` of each cache.
     */
    DSCacheFactory.keySet = function () {
      var cacheIds = {}, cacheId;
      for (cacheId in caches) {
        if (caches.hasOwnProperty(cacheId)) {
          cacheIds[cacheId] = cacheId;
        }
      }
      return cacheIds;
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:keys
     * @name keys
     * @description
     * Return an array containing the `cacheId` of each cache.
     * @returns {array} An array containing the `cacheId` of each cache.
     */
    DSCacheFactory.keys = function () {
      return _keys(caches);
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:destroyAll
     * @name destroyAll
     * @description
     * Destroy all caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.destroyAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache');
     * var otherCache = DSCacheFactory('otherCache');
     *
     * newCache.info().size; // 0
     * otherCache.info().size; // 0
     *
     * newCache.put('1', 'apple');
     * newCache.put('2', 'banana');
     * otherCache.put('abcd', 'horse');
     *
     * newCache.info().size; // 2
     * otherCache.info().size; // 1
     *
     * DSCacheFactory.destroyAll();
     *
     * newCache.info().size; // Error thrown
     * otherCache.info().size; // Error thrown
     *
     * DSCacheFactory.get('newCache'); // undefined
     * DSCacheFactory.get('otherCache'); // undefined
     * ```
     */
    DSCacheFactory.destroyAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].destroy();
      }
      caches = {};
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:clearAll
     * @name clearAll
     * @description
     * Clear the contents of all caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.clearAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache');
     * var otherCache = DSCacheFactory('otherCache');
     *
     * newCache.info().size; // 0
     * otherCache.info().size; // 0
     *
     * newCache.put('1', 'apple');
     * newCache.put('2', 'banana');
     * otherCache.put('abcd', 'horse');
     *
     * newCache.info().size; // 2
     * otherCache.info().size; // 1
     *
     * DSCacheFactory.clearAll();
     *
     * newCache.info().size; // 0
     * otherCache.info().size; // 0
     * ```
     */
    DSCacheFactory.clearAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].removeAll();
      }
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:enableAll
     * @name enableAll
     * @description
     * Enable any disabled caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.enableAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache', { disabled: true });
     * var otherCache = DSCacheFactory('otherCache', { disabled: true });
     *
     * newCache.info().disabled; // true
     * otherCache.info().disabled; // true
     *
     * DSCacheFactory.enableAll();
     *
     * newCache.info().disabled; // false
     * otherCache.info().disabled; // false
     * ```
     */
    DSCacheFactory.enableAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].$$disabled = false;
      }
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:disableAll
     * @name disableAll
     * @description
     * Disable all caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.disableAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache');
     * var otherCache = DSCacheFactory('otherCache');
     *
     * newCache.info().disabled; // false
     * otherCache.info().disabled; // false
     *
     * DSCacheFactory.disableAll();
     *
     * newCache.info().disabled; // true
     * otherCache.info().disabled; // true
     * ```
     */
    DSCacheFactory.disableAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].$$disabled = true;
      }
    };

    return DSCacheFactory;
  }];
}

module.exports = DSCacheFactoryProvider;

},{"../DSCache":4,"../defaults":19}],19:[function(require,module,exports){
var defaults = {
  /**
   * @doc overview
   * @id capacity
   * @name capacity
   * @description
   * __Default:__ `Number.MAX_VALUE`
   *
   * This option limits the capacity of a cache. With a maximum capacity set, a cache operates as an LRU cache,
   * deleting the least-recently-used item when the cache exceeds capacity.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setCapacity(capacity)`
   * - `DSCache.setOptions(options[, strict])`
   */
  capacity: Number.MAX_VALUE,

  /**
   * @doc overview
   * @id maxAge
   * @name maxAge
   * @description
   * __Default:__ `Number.MAX_VALUE`
   *
   * This option determines how long an item is in a cache before the item expires.. With `maxAge` set, items are
   * marked as expired when their time in a cache exceeds `maxAge`. A cache's behavior when an item expires is
   * determined by the [deleteOnExpire](/documentation/api/angular-cache/deleteOnExpire) option.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setMaxAge(maxAge)`
   * - `DSCache.setOptions(options[, strict])`
   */
  maxAge: Number.MAX_VALUE,

  /**
   * @doc overview
   * @id deleteOnExpire
   * @name deleteOnExpire
   * @description
   * __Default:__ `"none"`
   *
   * This option determines how long an item is in a cache before the item expires.. With `maxAge` set, items are
   * marked as expired when their time in a cache exceeds `maxAge`. A cache's behavior when an item expires is
   * determined by the [deleteOnExpire](/documentation/api/angular-cache/deleteOnExpire) option.
   *
   * This option is dynamically configurable. Must be `"none"`, `"passive"` or `"aggressive"`.
   *
   * #### "none"
   * A cache will do nothing when its items expire.
   *
   * #### "passive"
   * A cache will do nothing when its items expire. If an expired item is request it is removed from the cache and
   * `undefined` is returned.
   *
   * #### "aggressive"
   * A cache will periodically scan for expired items and actively remove them from the cache if any are found. The
   * frequency of the scan is determined by the [recycleFreq](/documentation/api/angular-cache/recycleFreq) option.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setRecycleFreq(recycleFreq)`
   * - `DSCache.setOptions(options[, strict])`
   */
  deleteOnExpire: 'none',

  /**
   * @doc overview
   * @id onExpire
   * @name onExpire
   * @description
   * __Default:__ `"none"`
   *
   * This option is a callback function which will be executed whenever an expired item is removed from a cache by
   * either requesting an expired item while the cache is in `"passive"` `deleteOnExpire` mode, or when an expired
   * item is actively removed when the cache is in `"aggressive"` `deleteOnExpire` mode.
   *
   * This option is dynamically configurable. Must be a function. Will be passed the `key` and `value` of the expired
   * item. Will be passed a third `done` argument (if in `"passive"` `deleteOnExpire` mode) which is the `onExpire`
   * argument passed to [DSCache#get(key[, options])](/documentation/api/angular-cache/DSCache.methods:get).
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setOnExpire(onExpire)`
   * - `DSCache.setOptions(options[, strict])`
   */
  onExpire: null,

  /**
   * @doc overview
   * @id cacheFlushInterval
   * @name cacheFlushInterval
   * @description
   * __Default:__ `null`
   *
   * This option, if set, will cause a cache to periodically clear itself of all data.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setCacheFlushInterval(cacheFlushInterval)`
   * - `DSCache.setOptions(options[, strict])`
   */
  cacheFlushInterval: null,

  /**
   * @doc overview
   * @id recycleFreq
   * @name recycleFreq
   * @description
   * __Default:__ `1000`
   *
   * This option determines how often a cache will scan for expired items when in `"aggressive"` `deleteOnExpire`
   * mode.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setRecycleFreq(recycleFreq)`
   * - `DSCache.setOptions(options[, strict])`
   */
  recycleFreq: 1000,

  /**
   * @doc overview
   * @id storageMode
   * @name storageMode
   * @description
   * __Default:__ `"memory"`
   *
   * This option determines the storage mode for a cache.
   *
   * #### "memory"
   * All data will be held in memory.
   *
   * #### "localStorage"
   * Data will be held in `localStorage`, if available (or
   * [storageImpl](/documentation/api/angular-cache/storageImpl) is provided).
   *
   * #### "sessionStorage"
   * Data will be held in `sessionStorage`, if available (or
   * [storageImpl](/documentation/api/angular-cache/storageImpl) is provided).
   *
   * This option is NOT dynamically configurable. Must be `"memory"`, `"localStorage"` or `"sessionStorage"`.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storageMode: 'memory',

  /**
   * @doc overview
   * @id storageImpl
   * @name storageImpl
   * @description
   * __Default:__ `null`
   *
   * This option is available if you want to provide a custom `localStorage` or `sessionStorage` implementation.
   *
   * This option is NOT dynamically configurable. Must be an object that implements `setItem(key, value)`,
   * `getItem(key)` and `removeItem(key)`.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storageImpl: null,

  /**
   * @doc overview
   * @id disabled
   * @name disabled
   * @description
   * __Default:__ `false`
   *
   * This option disables or enables cache.
   *
   * This option is dynamically configurable. Must be `true` or `false`.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setOptions(options[, strict])`
   *
   * or just use [DSCache#disable()](/documentation/api/angular-cache/DSCache.methods:disable) or
   * [DSCache#enable()](/documentation/api/angular-cache/DSCache.methods:enable).
   */
  disabled: false,

  /**
   * @doc overview
   * @id storagePrefix
   * @name storagePrefix
   * @description
   * __Default:__ `"angular-cache.caches."`
   *
   * This option determines the namespace for a cache when `storageMode` is `"localStorage"` or `"sessionStorage"`.
   * Setting this value to something like `"ac."` will save space when using WebStorage.
   *
   * This option is NOT dynamically configurable. Must be a string.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storagePrefix: 'angular-cache.caches.',

  /**
   * @doc overview
   * @id storeOnResolve
   * @name storeOnResolve
   * @description
   * __Default:__ `false`
   *
   * If putting a promise, also put the resolved value if the promise resolves.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setOptions(options[, strict])`
   */
  storeOnResolve: false,

  /**
   * @doc overview
   * @id storeOnReject
   * @name storeOnReject
   * @description
   * __Default:__ `false`
   *
   * If putting a promise, also put the rejection value if the the promise rejects.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storeOnReject: false
};

function Config() {
}

for (var option in defaults) {
  Config.prototype['$$' + option] = defaults[option];
}

module.exports = {
  Config: Config,
  defaults: defaults
};

},{}],20:[function(require,module,exports){
(function (window, angular, undefined) {
  'use strict';

  angular.$$minErr = angular.$$minErr || function minErr(module) {
    return function () {
      var code = arguments[0],
        prefix = '[' + (module ? module + ':' : '') + code + '] ',
        template = arguments[1],
        templateArgs = arguments,
        stringify = function (obj) {
          if (typeof obj === 'function') {
            return obj.toString().replace(/ \{[\s\S]*$/, '');
          } else if (typeof obj === 'undefined') {
            return 'undefined';
          } else if (typeof obj !== 'string') {
            return JSON.stringify(obj);
          }
          return obj;
        },
        message, i;

      message = prefix + template.replace(/\{\d+\}/g, function (match) {
        var index = +match.slice(1, -1), arg;

        if (index + 2 < templateArgs.length) {
          arg = templateArgs[index + 2];
          if (typeof arg === 'function') {
            return arg.toString().replace(/ ?\{[\s\S]*$/, '');
          } else if (typeof arg === 'undefined') {
            return 'undefined';
          } else if (typeof arg !== 'string') {
            return angular.toJson(arg);
          }
          return arg;
        }
        return match;
      });

      message = message + '\nhttp://errors.angularjs.org/' + angular.version.full + '/' +
        (module ? module + '/' : '') + code;
      for (i = 2; i < arguments.length; i++) {
        message = message + (i == 2 ? '?' : '&') + 'p' + (i - 2) + '=' +
          encodeURIComponent(stringify(arguments[i]));
      }

      return new Error(message);
    };
  };


  angular.module('angular-data.DSBinaryHeap', [])
    .provider('DSBinaryHeap', require('./DSBinaryHeap').DSBinaryHeapProvider);

  /**
   * @doc overview
   * @id angular-cache
   * @name Overview
   * @description
   * __Version:__ 3.2.2
   *
   * ## Install
   *
   * #### Bower
   * ```text
   * bower install angular-cache
   * ```
   *
   * Load `dist/angular-cache.js` or `dist/angular-cache.min.js` onto your web page after Angular.js.
   *
   * #### Npm
   * ```text
   * npm install angular-cache
   * ```
   *
   * Load `dist/angular-cache.js` or `dist/angular-cache.min.js` onto your web page after Angular.js. Angular-cache is
   * also consumable by Browserify and you should be able to `require('angular-cache')`. The `main` file is `src/index.js`.
   *
   * #### Manual download
   * Download angular-cache.3.2.2.js from the [Releases](https://github.com/jmdobry/angular-cache/releases)
   * section of the angular-cache GitHub project.
   *
   * ## Load into Angular
   * Your Angular app must depend on the module `"angular-data.DSCacheFactory"` in order to use angular-cache. Loading
   * angular-cache into your app allows you to inject the following:
   *
   * - `DSCacheFactory`
   * - `DSBinaryHeap`
   *
   * [DSCacheFactory](/documentation/api/api/DSCacheFactory) is a factory function that produces instances of
   * [DSCache](/documentation/api/api/DSCache), which is API compatible with caches produced by Angular's
   * [$cacheFactory](http://docs.angularjs.org/api/ng/service/$cacheFactory).
   *
   * [DSBinaryHeap](/documentation/api/api/DSBinaryHeap) is a priority queue implemented as a Binary Heap.
   *
   * Angular-cache is a dependency of [angular-data](/documentation/api/api/angular-data) and must be loaded before
   * angular-data if you are using angular-data.
   */
  angular.module('angular-data.DSCacheFactory', ['ng', 'angular-data.DSBinaryHeap'])
    .provider('DSCacheFactory', require('./DSCacheFactory'));

})(window, window.angular);

},{"./DSBinaryHeap":1,"./DSCacheFactory":18}],21:[function(require,module,exports){
module.exports = {
  /*!
   * Stringify a number.
   */
  stringifyNumber: function (number) {
    if (angular.isNumber(number)) {
      return number.toString();
    }
    return number;
  },

  /*!
   * Return a hash of the keys in the given collection.
   */
  keySet: function (collection) {
    var keySet = {}, key;
    for (key in collection) {
      if (collection.hasOwnProperty(key)) {
        keySet[key] = key;
      }
    }
    return keySet;
  },

  /*!
   * Return an array of the keys in the given collection
   */
  keys: function (collection) {
    var keys = [], key;
    for (key in collection) {
      if (collection.hasOwnProperty(key)) {
        keys.push(key);
      }
    }
    return keys;
  }
};

},{}]},{},[20]);
