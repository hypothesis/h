// Generated by CoffeeScript 1.6.3
/*
** Annotator 1.2.6-dev-272fa6d
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-11-14 10:14:26Z
*/



/*
//
*/

// Generated by CoffeeScript 1.6.3
(function() {
  var _ref,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  window.PDFTextMapper = (function(_super) {
    __extends(PDFTextMapper, _super);

    PDFTextMapper.applicable = function() {
      var _ref;
      return (_ref = typeof PDFView !== "undefined" && PDFView !== null ? PDFView.initialized : void 0) != null ? _ref : false;
    };

    PDFTextMapper.prototype.requiresSmartStringPadding = true;

    PDFTextMapper.prototype.getPageCount = function() {
      return PDFView.pages.length;
    };

    PDFTextMapper.prototype.getPageIndex = function() {
      return PDFView.page - 1;
    };

    PDFTextMapper.prototype.setPageIndex = function(index) {
      return PDFView.page = index + 1;
    };

    PDFTextMapper.prototype._isPageRendered = function(index) {
      var _ref, _ref1;
      return (_ref = PDFView.pages[index]) != null ? (_ref1 = _ref.textLayer) != null ? _ref1.renderingDone : void 0 : void 0;
    };

    PDFTextMapper.prototype.getRootNodeForPage = function(index) {
      return PDFView.pages[index].textLayer.textLayerDiv;
    };

    function PDFTextMapper() {
      this._parseExtractedText = __bind(this._parseExtractedText, this);
      this.setEvents();
    }

    PDFTextMapper.prototype.setEvents = function() {
      var _this = this;
      addEventListener("pagerender", function(evt) {
        var index;
        if (_this.pageInfo == null) {
          return;
        }
        index = evt.detail.pageNumber - 1;
        return _this._onPageRendered(index);
      });
      addEventListener("DOMNodeRemoved", function(evt) {
        var index, node;
        node = evt.target;
        if (node.nodeType === Node.ELEMENT_NODE && node.nodeName.toLowerCase() === "div" && node.className === "textLayer") {
          index = parseInt(node.parentNode.id.substr(13) - 1);
          return _this._unmapPage(_this.pageInfo[index]);
        }
      });
      window.DomTextMapper.instances.push({
        id: "cross-page catcher",
        rootNode: document.getElementById("viewer"),
        performUpdateOnNode: function(node, data) {
          var endPage, index, startPage, _i, _ref, _ref1, _results;
          if ("viewer" === (typeof node.getAttribute === "function" ? node.getAttribute("id") : void 0)) {
            if ((data.start != null) && (data.end != null)) {
              startPage = _this.getPageForNode(data.start);
              endPage = _this.getPageForNode(data.end);
              _results = [];
              for (index = _i = _ref = startPage.index, _ref1 = endPage.index; _ref <= _ref1 ? _i <= _ref1 : _i >= _ref1; index = _ref <= _ref1 ? ++_i : --_i) {
                _results.push(_this._updateMap(_this.pageInfo[index]));
              }
              return _results;
            }
          }
        },
        documentChanged: function() {},
        timestamp: function() {}
      });
      return $(PDFView.container).on('scroll', function() {
        return _this._onScroll();
      });
    };

    PDFTextMapper.prototype._extractionPattern = /[ ]+/g;

    PDFTextMapper.prototype._parseExtractedText = function(text) {
      return text.replace(this._extractionPattern, " ");
    };

    PDFTextMapper.prototype.scan = function() {
      var _this = this;
      if (this.pendingScan == null) {
        this.pendingScan = new PDFJS.Promise();
      }
      if (PDFView.pdfDocument == null) {
        setTimeout((function() {
          return _this.scan();
        }), 500);
        return this.pendingScan;
      }
      PDFView.getPage(1).then(function() {
        console.log("Scanning document for text...");
        PDFFindController.extractText();
        return PDFJS.Promise.all(PDFFindController.extractTextPromises).then(function() {
          var page;
          _this.pageInfo = (function() {
            var _i, _len, _ref, _results;
            _ref = PDFFindController.pageContents;
            _results = [];
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
              page = _ref[_i];
              _results.push({
                content: this._parseExtractedText(page)
              });
            }
            return _results;
          }).call(_this);
          _this._onHavePageContents();
          _this.pendingScan.resolve();
          return _this._onAfterScan();
        });
      });
      return this.pendingScan;
    };

    PDFTextMapper.prototype.getPageForNode = function(node) {
      var div, index;
      div = node;
      while ((div.nodeType !== Node.ELEMENT_NODE) || (div.getAttribute("class") == null) || (div.getAttribute("class") !== "textLayer")) {
        div = div.parentNode;
      }
      index = parseInt(div.parentNode.id.substr(13) - 1);
      return this.pageInfo[index];
    };

    return PDFTextMapper;

  })(window.PageTextMapperCore);

  Annotator.Plugin.PDF = (function(_super) {
    __extends(PDF, _super);

    function PDF() {
      _ref = PDF.__super__.constructor.apply(this, arguments);
      return _ref;
    }

    PDF.prototype.pluginInit = function() {
      return this.annotator.documentAccessStrategies.unshift({
        name: "PDF.js",
        mapper: PDFTextMapper
      });
    };

    return PDF;

  })(Annotator.Plugin);

}).call(this);

//
//@ sourceMappingURL=annotator.pdf.map