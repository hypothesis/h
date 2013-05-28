/*
** Annotator 1.2.6-dev-b61d9f7
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-05-28 12:14:39Z
*/


(function() {
  var _ref,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  Annotator.Plugin.Document = (function(_super) {
    var $;

    __extends(Document, _super);

    function Document() {
      this._getFavicon = __bind(this._getFavicon, this);
      this._getLinks = __bind(this._getLinks, this);
      this._getTitle = __bind(this._getTitle, this);
      this._getOpenGraph = __bind(this._getOpenGraph, this);
      this._getDublinCore = __bind(this._getDublinCore, this);
      this._getScholar = __bind(this._getScholar, this);
      this.getDocumentMetadata = __bind(this.getDocumentMetadata, this);
      this.beforeAnnotationCreated = __bind(this.beforeAnnotationCreated, this);
      this.uris = __bind(this.uris, this);
      this.uri = __bind(this.uri, this);      _ref = Document.__super__.constructor.apply(this, arguments);
      return _ref;
    }

    $ = Annotator.$;

    Document.prototype.events = {
      'beforeAnnotationCreated': 'beforeAnnotationCreated'
    };

    Document.prototype.pluginInit = function() {
      return this.getDocumentMetadata();
    };

    Document.prototype.uri = function() {
      var link, uri, _i, _len, _ref1;

      uri = decodeURIComponent(document.location.href);
      _ref1 = this.metadata;
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        link = _ref1[_i];
        if (link.rel === "canonical") {
          uri = link.href;
        }
      }
      return uri;
    };

    Document.prototype.uris = function() {
      var href, link, uniqueUrls, _i, _len, _ref1;

      uniqueUrls = {};
      _ref1 = this.metadata.link;
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        link = _ref1[_i];
        if (link.href) {
          uniqueUrls[link.href] = true;
        }
      }
      return (function() {
        var _results;

        _results = [];
        for (href in uniqueUrls) {
          _results.push(href);
        }
        return _results;
      })();
    };

    Document.prototype.beforeAnnotationCreated = function(annotation) {
      return annotation.document = this.metadata;
    };

    Document.prototype.getDocumentMetadata = function() {
      this.metadata = {};
      this._getScholar();
      this._getDublinCore();
      this._getOpenGraph();
      this._getFavicon();
      this._getTitle();
      this._getLinks();
      return this.metadata;
    };

    Document.prototype._getScholar = function() {
      var content, meta, name, _i, _len, _ref1, _results;

      this.metadata.scholar = {};
      _ref1 = $("meta");
      _results = [];
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        meta = _ref1[_i];
        name = $(meta).prop("name");
        content = $(meta).prop("content");
        if (name.match(/^citation_/)) {
          if (this.metadata.scholar[name]) {
            _results.push(this.metadata.scholar[name].push(content));
          } else {
            _results.push(this.metadata.scholar[name] = [content]);
          }
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    Document.prototype._getDublinCore = function() {
      var content, meta, n, name, nameParts, _i, _len, _ref1, _results;

      this.metadata.dc = {};
      _ref1 = $("meta");
      _results = [];
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        meta = _ref1[_i];
        name = $(meta).prop("name");
        content = $(meta).prop("content");
        nameParts = name.split(".");
        if (nameParts.length === 2 && nameParts[0].toLowerCase() === "dc") {
          n = nameParts[1];
          if (this.metadata.dc[n]) {
            _results.push(this.metadata.dc[n].push(content));
          } else {
            _results.push(this.metadata.dc[n] = [content]);
          }
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    Document.prototype._getOpenGraph = function() {
      var content, match, meta, n, property, _i, _len, _ref1, _results;

      this.metadata.og = {};
      _ref1 = $("meta");
      _results = [];
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        meta = _ref1[_i];
        property = $(meta).attr("property");
        content = $(meta).prop("content");
        if (property) {
          match = property.match(/^og:(.+)$/);
          if (match) {
            n = match[1];
            if (this.metadata.og[n]) {
              _results.push(this.metadata.og[n].push(content));
            } else {
              _results.push(this.metadata.og[n] = [content]);
            }
          } else {
            _results.push(void 0);
          }
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    Document.prototype._getTitle = function() {
      if (this.metadata.scholar.citation_title) {
        return this.metadata.title = this.metadata.scholar.citation_title[0];
      } else if (this.metadata.dc.title) {
        return this.metadata.title = this.metadata.dc.title;
      } else {
        return this.metadata.title = $("head title").text();
      }
    };

    Document.prototype._getLinks = function() {
      var doi, href, id, l, link, name, rel, type, url, values, _i, _j, _k, _len, _len1, _len2, _ref1, _ref2, _ref3, _results;

      this.metadata.link = [
        {
          href: document.location.href
        }
      ];
      _ref1 = $("link");
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        link = _ref1[_i];
        l = $(link);
        href = this._absoluteUrl(l.prop('href'));
        rel = l.prop('rel');
        type = l.prop('type');
        if ((rel === "alternate" || rel === "canonical" || rel === "bookmark") && (type !== "application/rss+xml" && type !== "application/atom+xml")) {
          this.metadata.link.push({
            href: href,
            rel: rel,
            type: type
          });
        }
      }
      _ref2 = this.metadata.scholar;
      for (name in _ref2) {
        values = _ref2[name];
        if (name === "citation_pdf_url") {
          for (_j = 0, _len1 = values.length; _j < _len1; _j++) {
            url = values[_j];
            this.metadata.link.push({
              href: this._absoluteUrl(url),
              type: "application/pdf"
            });
          }
        }
        if (name === "citation_doi") {
          for (_k = 0, _len2 = values.length; _k < _len2; _k++) {
            doi = values[_k];
            if (doi.slice(0, 4) !== "doi:") {
              doi = "doi:" + doi;
            }
            this.metadata.link.push({
              href: doi
            });
          }
        }
      }
      _ref3 = this.metadata.dc;
      _results = [];
      for (name in _ref3) {
        values = _ref3[name];
        if (name === "identifier") {
          _results.push((function() {
            var _l, _len3, _results1;

            _results1 = [];
            for (_l = 0, _len3 = values.length; _l < _len3; _l++) {
              id = values[_l];
              if (id.slice(0, 4) === "doi:") {
                _results1.push(this.metadata.link.push({
                  href: id
                }));
              } else {
                _results1.push(void 0);
              }
            }
            return _results1;
          }).call(this));
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    Document.prototype._getFavicon = function() {
      var link, _i, _len, _ref1, _ref2, _results;

      _ref1 = $("link");
      _results = [];
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        link = _ref1[_i];
        if ((_ref2 = $(link).prop("rel")) === "shortcut icon" || _ref2 === "icon") {
          _results.push(this.metadata["favicon"] = this._absoluteUrl(link.href));
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    Document.prototype._absoluteUrl = function(url) {
      var img;

      img = $("<img src='" + url + "'>");
      url = img.prop('src');
      img.prop('src', null);
      return url;
    };

    return Document;

  })(Annotator.Plugin);

}).call(this);
