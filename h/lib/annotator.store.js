/*
** Annotator 1.2.5-dev-a12bec5
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-03-04 18:10:13Z
*/

(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; },
    __indexOf = Array.prototype.indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  Annotator.Plugin.Store = (function(_super) {

    __extends(Store, _super);

    Store.prototype.events = {
      'annotationCreated': 'annotationCreated',
      'annotationDeleted': 'annotationDeleted',
      'annotationUpdated': 'annotationUpdated'
    };

    Store.prototype.options = {
      prefix: '/store',
      autoFetch: true,
      annotationData: {},
      loadFromSearch: false,
      urls: {
        create: '/annotations',
        read: '/annotations/:id',
        update: '/annotations/:id',
        destroy: '/annotations/:id',
        search: '/search'
      }
    };

    function Store(element, options) {
      this._onError = __bind(this._onError, this);
      this._onLoadAnnotationsFromSearch = __bind(this._onLoadAnnotationsFromSearch, this);
      this._onLoadAnnotations = __bind(this._onLoadAnnotations, this);
      this._getAnnotations = __bind(this._getAnnotations, this);      Store.__super__.constructor.apply(this, arguments);
      this.annotations = [];
    }

    Store.prototype.pluginInit = function() {
      if (!Annotator.supported()) return;
      if (this.annotator.plugins.Auth) {
        return this.annotator.plugins.Auth.withToken(this._getAnnotations);
      } else {
        return this._getAnnotations();
      }
    };

    Store.prototype._getAnnotations = function() {
      if (this.options.loadFromSearch) {
        return this.loadAnnotationsFromSearch(this.options.loadFromSearch);
      } else {
        return this.loadAnnotations();
      }
    };

    Store.prototype.annotationCreated = function(annotation) {
      var quote,
        _this = this;
      if (__indexOf.call(this.annotations, annotation) < 0) {
        this.registerAnnotation(annotation);
        quote = annotation.quote;
        delete annotation.quote;
        return this._apiRequest('create', annotation, function(data) {
          annotation.quote = quote;
          if (!(data.id != null)) {
            console.warn(Annotator._t("Warning: No ID returned from server for annotation "), annotation);
          }
          return _this.updateAnnotation(annotation, data);
        });
      } else {
        return this.updateAnnotation(annotation, {});
      }
    };

    Store.prototype.annotationUpdated = function(annotation) {
      var quote,
        _this = this;
      if (__indexOf.call(this.annotations, annotation) >= 0) {
        quote = annotation.quote;
        return this._apiRequest('update', annotation, (function(data) {
          annotation.quote = quote;
          return _this.updateAnnotation(annotation, data);
        }));
      }
    };

    Store.prototype.annotationDeleted = function(annotation) {
      var _this = this;
      if (__indexOf.call(this.annotations, annotation) >= 0) {
        return this._apiRequest('destroy', annotation, (function() {
          return _this.unregisterAnnotation(annotation);
        }));
      }
    };

    Store.prototype.registerAnnotation = function(annotation) {
      return this.annotations.push(annotation);
    };

    Store.prototype.unregisterAnnotation = function(annotation) {
      return this.annotations.splice(this.annotations.indexOf(annotation), 1);
    };

    Store.prototype.updateAnnotation = function(annotation, data) {
      if (__indexOf.call(this.annotations, annotation) < 0) {
        console.error(Annotator._t("Trying to update unregistered annotation!"));
      } else {
        $.extend(annotation, data);
      }
      return $(annotation.highlights).data('annotation', annotation);
    };

    Store.prototype.loadAnnotations = function() {
      return this._apiRequest('read', null, this._onLoadAnnotations);
    };

    Store.prototype._onLoadAnnotations = function(data) {
      if (data == null) data = [];
      this.annotations = data;
      return this.annotator.loadAnnotations(data.slice());
    };

    Store.prototype.loadAnnotationsFromSearch = function(searchOptions) {
      return this._apiRequest('search', searchOptions, this._onLoadAnnotationsFromSearch);
    };

    Store.prototype._onLoadAnnotationsFromSearch = function(data) {
      if (data == null) data = {};
      return this._onLoadAnnotations(data.rows || []);
    };

    Store.prototype.dumpAnnotations = function() {
      var ann, _i, _len, _ref, _results;
      _ref = this.annotations;
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        ann = _ref[_i];
        _results.push(JSON.parse(this._dataFor(ann)));
      }
      return _results;
    };

    Store.prototype._apiRequest = function(action, obj, onSuccess) {
      var id, options, request, url;
      id = obj && obj.id;
      url = this._urlFor(action, id);
      options = this._apiRequestOptions(action, obj, onSuccess);
      request = $.ajax(url, options);
      request._id = id;
      request._action = action;
      return request;
    };

    Store.prototype._apiRequestOptions = function(action, obj, onSuccess) {
      var opts;
      opts = {
        type: this._methodFor(action),
        headers: this.element.data('annotator:headers'),
        dataType: "json",
        success: onSuccess || function() {},
        error: this._onError
      };
      if (action === "search") {
        opts = $.extend(opts, {
          data: obj
        });
      } else {
        opts = $.extend(opts, {
          data: obj && this._dataFor(obj),
          contentType: "application/json; charset=utf-8"
        });
      }
      return opts;
    };

    Store.prototype._urlFor = function(action, id) {
      var replaceWith, url;
      replaceWith = id != null ? '/' + id : '';
      url = this.options.prefix || '/';
      url += this.options.urls[action];
      url = url.replace(/\/:id/, replaceWith);
      return url;
    };

    Store.prototype._methodFor = function(action) {
      var table;
      table = {
        'create': 'POST',
        'read': 'GET',
        'update': 'PUT',
        'destroy': 'DELETE',
        'search': 'GET'
      };
      return table[action];
    };

    Store.prototype._dataFor = function(annotation) {
      var data, highlights;
      highlights = annotation.highlights;
      delete annotation.highlights;
      $.extend(annotation, this.options.annotationData);
      data = JSON.stringify(annotation);
      if (highlights) annotation.highlights = highlights;
      return data;
    };

    Store.prototype._onError = function(xhr) {
      var action, message;
      action = xhr._action;
      message = Annotator._t("Sorry we could not ") + action + Annotator._t(" this annotation");
      if (xhr._action === 'search') {
        message = Annotator._t("Sorry we could not search the store for annotations");
      } else if (xhr._action === 'read' && !xhr._id) {
        message = Annotator._t("Sorry we could not ") + action + Annotator._t(" the annotations from the store");
      }
      switch (xhr.status) {
        case 401:
          message = Annotator._t("Sorry you are not allowed to ") + action + Annotator._t(" this annotation");
          break;
        case 404:
          message = Annotator._t("Sorry we could not connect to the annotations store");
          break;
        case 500:
          message = Annotator._t("Sorry something went wrong with the annotation store");
      }
      Annotator.showNotification(message, Annotator.Notification.ERROR);
      return console.error(Annotator._t("API request failed:") + (" '" + xhr.status + "'"));
    };

    return Store;

  })(Annotator.Plugin);

}).call(this);
