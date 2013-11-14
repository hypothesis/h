// Generated by CoffeeScript 1.6.3
/*
** Annotator 1.2.6-dev-e65efcd
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-11-14 11:56:23Z
*/



/*
//
*/

// Generated by CoffeeScript 1.6.3
(function() {
  var TextHighlight, TextRangeAnchor, _ref,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  TextHighlight = (function(_super) {
    __extends(TextHighlight, _super);

    TextHighlight.isInstance = function(element) {
      return $(element).hasClass('annotator-hl');
    };

    TextHighlight.getIndependentParent = function(element) {
      return $(element).parents(':not([class^=annotator-hl])')[0];
    };

    TextHighlight._inited = [];

    TextHighlight._init = function(annotator) {
      var getAnnotations,
        _this = this;
      if (__indexOf.call(this._inited, annotator) >= 0) {
        return;
      }
      getAnnotations = function(event) {
        var annotations;
        return annotations = $(event.target).parents('.annotator-hl').andSelf().map(function() {
          return $(this).data("annotation");
        });
      };
      annotator.addEvent(".annotator-hl", "mouseover", function(event) {
        return annotator.onAnchorMouseover(getAnnotations(event));
      });
      annotator.addEvent(".annotator-hl", "mouseout", function(event) {
        return annotator.onAnchorMouseout(getAnnotations(event));
      });
      annotator.addEvent(".annotator-hl", "mousedown", function(event) {
        return annotator.onAnchorMousedown(getAnnotations(event));
      });
      annotator.addEvent(".annotator-hl", "click", function(event) {
        return annotator.onAnchorClick(getAnnotations(event));
      });
      return this._inited.push(annotator);
    };

    TextHighlight.prototype._highlightRange = function(normedRange, cssClass) {
      var hl, node, r, white, _i, _len, _ref, _results;
      if (cssClass == null) {
        cssClass = 'annotator-hl';
      }
      white = /^\s*$/;
      hl = $("<span class='" + cssClass + "'></span>");
      _ref = normedRange.textNodes();
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        node = _ref[_i];
        if (!(!white.test(node.nodeValue))) {
          continue;
        }
        r = $(node).wrapAll(hl).parent().show()[0];
        window.DomTextMapper.changed(node, "created hilite");
        _results.push(r);
      }
      return _results;
    };

    TextHighlight.prototype._highlightRanges = function(normedRanges, cssClass) {
      var highlights, r, _i, _len;
      if (cssClass == null) {
        cssClass = 'annotator-hl';
      }
      highlights = [];
      for (_i = 0, _len = normedRanges.length; _i < _len; _i++) {
        r = normedRanges[_i];
        $.merge(highlights, this._highlightRange(r, cssClass));
      }
      return highlights;
    };

    function TextHighlight(annotator, annotation, pageIndex, realRange) {
      var browserRange, range;
      TextHighlight._init(annotator);
      TextHighlight.__super__.constructor.call(this, annotator, annotation, pageIndex);
      browserRange = new Annotator.Range.BrowserRange(realRange);
      range = browserRange.normalize(this.annotator.wrapper[0]);
      this._highlights = this._highlightRange(range);
      $(this._highlights).data("annotation", annotation);
    }

    TextHighlight.prototype.isTemporary = function() {
      return this._temporary;
    };

    TextHighlight.prototype.setTemporary = function(value) {
      this._temporary = value;
      if (value) {
        return $(this._highlights).addClass('annotator-hl-temporary');
      } else {
        return $(this._highlights).removeClass('annotator-hl-temporary');
      }
    };

    TextHighlight.prototype.setActive = function(value) {
      if (value) {
        return $(this._highlights).addClass('annotator-hl-active');
      } else {
        return $(this._highlights).removeClass('annotator-hl-active');
      }
    };

    TextHighlight.prototype.removeFromDocument = function() {
      var child, hl, _i, _len, _ref, _results;
      _ref = this._highlights;
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        hl = _ref[_i];
        if ((hl.parentNode != null) && this.annotator.domMapper.isPageMapped(this.pageIndex)) {
          child = hl.childNodes[0];
          $(hl).replaceWith(hl.childNodes);
          _results.push(window.DomTextMapper.changed(child.parentNode, "removed hilite (annotation deleted)"));
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    TextHighlight.prototype._getDOMElements = function() {
      return this._highlights;
    };

    return TextHighlight;

  })(Annotator.Highlight);

  TextRangeAnchor = (function(_super) {
    __extends(TextRangeAnchor, _super);

    function TextRangeAnchor(annotator, annotation, target, start, end, startPage, endPage, quote, diffHTML, diffCaseOnly) {
      this.start = start;
      this.end = end;
      TextRangeAnchor.__super__.constructor.call(this, annotator, annotation, target, startPage, endPage, quote, diffHTML, diffCaseOnly);
      if (this.start == null) {
        throw "start is required!";
      }
      if (this.end == null) {
        throw "end is required!";
      }
    }

    TextRangeAnchor.prototype._createHighlight = function(page) {
      var mappings, range;
      mappings = this.annotator.domMapper.getMappingsForCharRange(this.start, this.end, [page]);
      range = mappings.sections[page].realRange;
      return new TextHighlight(this.annotator, this.annotation, page, range);
    };

    return TextRangeAnchor;

  })(Annotator.Anchor);

  Annotator.Plugin.TextAnchors = (function(_super) {
    __extends(TextAnchors, _super);

    function TextAnchors() {
      this.checkForEndSelection = __bind(this.checkForEndSelection, this);
      _ref = TextAnchors.__super__.constructor.apply(this, arguments);
      return _ref;
    }

    TextAnchors.prototype.pluginInit = function() {
      this.annotator.anchoringStrategies.push({
        name: "range",
        code: this.createFromRangeSelector
      });
      this.annotator.anchoringStrategies.push({
        name: "position",
        code: this.createFromPositionSelector
      });
      $(document).bind({
        "mouseup": this.checkForEndSelection
      });
      this.annotator.TextRangeAnchor = TextRangeAnchor;
      return null;
    };

    TextAnchors.prototype._getSelectedRanges = function() {
      var browserRange, i, normedRange, r, ranges, rangesToIgnore, selection, _i, _len;
      selection = Annotator.util.getGlobal().getSelection();
      ranges = [];
      rangesToIgnore = [];
      if (!selection.isCollapsed) {
        ranges = (function() {
          var _i, _ref1, _results;
          _results = [];
          for (i = _i = 0, _ref1 = selection.rangeCount; 0 <= _ref1 ? _i < _ref1 : _i > _ref1; i = 0 <= _ref1 ? ++_i : --_i) {
            r = selection.getRangeAt(i);
            browserRange = new Annotator.Range.BrowserRange(r);
            normedRange = browserRange.normalize().limit(this.annotator.wrapper[0]);
            if (normedRange === null) {
              rangesToIgnore.push(r);
            }
            _results.push(normedRange);
          }
          return _results;
        }).call(this);
        selection.removeAllRanges();
      }
      for (_i = 0, _len = rangesToIgnore.length; _i < _len; _i++) {
        r = rangesToIgnore[_i];
        selection.addRange(r);
      }
      return $.grep(ranges, function(range) {
        if (range) {
          selection.addRange(range.toRange());
        }
        return range;
      });
    };

    TextAnchors.prototype.checkForEndSelection = function(event) {
      var container, r, range, selectedRanges, _i, _len;
      this.annotator.mouseIsDown = false;
      if (this.annotator.ignoreMouseup) {
        return;
      }
      selectedRanges = this._getSelectedRanges();
      for (_i = 0, _len = selectedRanges.length; _i < _len; _i++) {
        range = selectedRanges[_i];
        container = range.commonAncestor;
        if (TextHighlight.isInstance(container)) {
          container = TextHighlight.getIndependentParent(container);
        }
        if (this.annotator.isAnnotator(container)) {
          return;
        }
      }
      this.annotator.selectedTargets = (function() {
        var _j, _len1, _results;
        _results = [];
        for (_j = 0, _len1 = selectedRanges.length; _j < _len1; _j++) {
          r = selectedRanges[_j];
          _results.push(this.getTargetFromRange(r));
        }
        return _results;
      }).call(this);
      if (event && selectedRanges.length) {
        return this.annotator.onSuccessfulSelection(event);
      } else {
        return this.annotator.onFailedSelection(event);
      }
    };

    TextAnchors.prototype._getRangeSelector = function(range) {
      var sr;
      sr = range.serialize(this.annotator.wrapper[0]);
      return {
        type: "RangeSelector",
        startContainer: sr.startContainer,
        startOffset: sr.startOffset,
        endContainer: sr.endContainer,
        endOffset: sr.endOffset
      };
    };

    TextAnchors.prototype._getTextQuoteSelector = function(range) {
      var endOffset, prefix, quote, rangeEnd, rangeStart, startOffset, suffix, _ref1;
      if (range == null) {
        throw new Error("Called getTextQuoteSelector(range) with null range!");
      }
      rangeStart = range.start;
      if (rangeStart == null) {
        throw new Error("Called getTextQuoteSelector(range) on a range with no valid start.");
      }
      startOffset = (this.annotator.domMapper.getInfoForNode(rangeStart)).start;
      rangeEnd = range.end;
      if (rangeEnd == null) {
        throw new Error("Called getTextQuoteSelector(range) on a range with no valid end.");
      }
      endOffset = (this.annotator.domMapper.getInfoForNode(rangeEnd)).end;
      quote = this.annotator.domMapper.getCorpus().slice(startOffset, +(endOffset - 1) + 1 || 9e9).trim();
      _ref1 = this.annotator.domMapper.getContextForCharRange(startOffset, endOffset), prefix = _ref1[0], suffix = _ref1[1];
      return {
        type: "TextQuoteSelector",
        exact: quote,
        prefix: prefix,
        suffix: suffix
      };
    };

    TextAnchors.prototype._getTextPositionSelector = function(range) {
      var endOffset, startOffset;
      startOffset = (this.annotator.domMapper.getInfoForNode(range.start)).start;
      endOffset = (this.annotator.domMapper.getInfoForNode(range.end)).end;
      return {
        type: "TextPositionSelector",
        start: startOffset,
        end: endOffset
      };
    };

    TextAnchors.prototype.getTargetFromRange = function(range) {
      return {
        source: this.annotator.getHref(),
        selector: [this._getRangeSelector(range), this._getTextQuoteSelector(range), this._getTextPositionSelector(range)]
      };
    };

    TextAnchors.prototype.getQuoteForTarget = function(target) {
      var selector;
      selector = this.annotator.findSelector(target.selector, "TextQuoteSelector");
      if (selector != null) {
        return this.annotator.normalizeString(selector.exact);
      } else {
        return null;
      }
    };

    TextAnchors.prototype.createFromRangeSelector = function(annotation, target) {
      var content, currentQuote, endInfo, endOffset, error, normalizedRange, savedQuote, selector, startInfo, startOffset, _ref1, _ref2;
      selector = this.findSelector(target.selector, "RangeSelector");
      if (selector == null) {
        return null;
      }
      try {
        normalizedRange = Range.sniff(selector).normalize(this.wrapper[0]);
      } catch (_error) {
        error = _error;
        return null;
      }
      startInfo = this.domMapper.getInfoForNode(normalizedRange.start);
      startOffset = startInfo.start;
      endInfo = this.domMapper.getInfoForNode(normalizedRange.end);
      endOffset = endInfo.end;
      content = this.domMapper.getCorpus().slice(startOffset, +(endOffset - 1) + 1 || 9e9).trim();
      currentQuote = this.normalizeString(content);
      savedQuote = this.plugins.TextAnchors.getQuoteForTarget(target);
      if ((savedQuote != null) && currentQuote !== savedQuote) {
        return null;
      }
      return new TextRangeAnchor(this, annotation, target, startInfo.start, endInfo.end, (_ref1 = startInfo.pageIndex) != null ? _ref1 : 0, (_ref2 = endInfo.pageIndex) != null ? _ref2 : 0, currentQuote);
    };

    TextAnchors.prototype.createFromPositionSelector = function(annotation, target) {
      var content, currentQuote, savedQuote, selector;
      selector = this.findSelector(target.selector, "TextPositionSelector");
      if (selector == null) {
        return null;
      }
      content = this.domMapper.getCorpus().slice(selector.start, +(selector.end - 1) + 1 || 9e9).trim();
      currentQuote = this.normalizeString(content);
      savedQuote = this.plugins.TextAnchors.getQuoteForTarget(target);
      if ((savedQuote != null) && currentQuote !== savedQuote) {
        return null;
      }
      return new TextRangeAnchor(this, annotation, target, selector.start, selector.end, this.domMapper.getPageIndexForPos(selector.start), this.domMapper.getPageIndexForPos(selector.end), currentQuote);
    };

    return TextAnchors;

  })(Annotator.Plugin);

}).call(this);

//
//@ sourceMappingURL=annotator.textanchors.map