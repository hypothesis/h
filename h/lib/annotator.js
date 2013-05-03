/*
** Annotator 1.2.6-dev-4f5b2f1
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-05-03 17:01:04Z
*/

(function() {
  var $, Annotator, Delegator, LinkParser, Range, fn, functions, g, gettext, util, _Annotator, _gettext, _i, _j, _len, _len2, _ref, _ref2, _t,
    __indexOf = Array.prototype.indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; },
    __slice = Array.prototype.slice,
    __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  window.DomTextMapper = (function() {
    var CONTEXT_LEN, SELECT_CHILDREN_INSTEAD, USE_EMPTY_TEXT_WORKAROUND, USE_TABLE_TEXT_WORKAROUND, WHITESPACE;

    USE_TABLE_TEXT_WORKAROUND = true;

    USE_EMPTY_TEXT_WORKAROUND = true;

    SELECT_CHILDREN_INSTEAD = ["thead", "tbody", "ol", "a", "caption", "p"];

    CONTEXT_LEN = 32;

    DomTextMapper.instances = [];

    DomTextMapper.changed = function(node, reason) {
      var instance, _i, _len, _ref;
      if (reason == null) reason = "no reason";
      if (this.instances.length === 0) return;
      _ref = this.instances;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        instance = _ref[_i];
        instance.performUpdateOnNode(node);
      }
      return null;
    };

    function DomTextMapper() {
      this.setRealRoot();
      window.DomTextMapper.instances.push(this);
    }

    DomTextMapper.prototype.setRootNode = function(rootNode) {
      this.rootWin = window;
      return this.pathStartNode = this.rootNode = rootNode;
    };

    DomTextMapper.prototype.setRootId = function(rootId) {
      return this.setRootNode(document.getElementById(rootId));
    };

    DomTextMapper.prototype.setRootIframe = function(iframeId) {
      var iframe;
      iframe = window.document.getElementById(iframeId);
      if (iframe == null) throw new Error("Can't find iframe with specified ID!");
      this.rootWin = iframe.contentWindow;
      if (this.rootWin == null) {
        throw new Error("Can't access contents of the spefified iframe!");
      }
      this.rootNode = this.rootWin.document;
      return this.pathStartNode = this.getBody();
    };

    DomTextMapper.prototype.getDefaultPath = function() {
      return this.getPathTo(this.pathStartNode);
    };

    DomTextMapper.prototype.setRealRoot = function() {
      this.rootWin = window;
      this.rootNode = document;
      return this.pathStartNode = this.getBody();
    };

    DomTextMapper.prototype.documentChanged = function() {
      return this.lastDOMChange = this.timestamp();
    };

    DomTextMapper.prototype.scan = function() {
      var node, path, startTime, t1, t2;
      if (this.domStableSince(this.lastScanned)) return this.path;
      startTime = this.timestamp();
      this.saveSelection();
      this.path = {};
      this.traverseSubTree(this.pathStartNode, this.getDefaultPath());
      t1 = this.timestamp();
      path = this.getPathTo(this.pathStartNode);
      node = this.path[path].node;
      this.collectPositions(node, path, null, 0, 0);
      this.restoreSelection();
      this.lastScanned = this.timestamp();
      this.corpus = this.path[path].content;
      t2 = this.timestamp();
      return this.path;
    };

    DomTextMapper.prototype.selectPath = function(path, scroll) {
      var info, node;
      if (scroll == null) scroll = false;
      info = this.path[path];
      if (info == null) throw new Error("I have no info about a node at " + path);
      node = info != null ? info.node : void 0;
      node || (node = this.lookUpNode(info.path));
      return this.selectNode(node, scroll);
    };

    DomTextMapper.prototype.performUpdateOnNode = function(node, escalating) {
      var data, oldIndex, p, parentNode, parentPath, parentPathInfo, path, pathInfo, pathsToDrop, prefix, startTime, _i, _len, _ref;
      if (escalating == null) escalating = false;
      if (node == null) throw new Error("Called performUpdate with a null node!");
      if (this.path == null) return;
      startTime = this.timestamp();
      if (!escalating) this.saveSelection();
      path = this.getPathTo(node);
      pathInfo = this.path[path];
      if (pathInfo == null) {
        this.performUpdateOnNode(node.parentNode, true);
        if (!escalating) this.restoreSelection();
        return;
      }
      if (pathInfo.node === node && pathInfo.content === this.getNodeContent(node, false)) {
        prefix = path + "/";
        pathsToDrop = p;
        pathsToDrop = [];
        _ref = this.path;
        for (p in _ref) {
          data = _ref[p];
          if (this.stringStartsWith(p, prefix)) pathsToDrop.push(p);
        }
        for (_i = 0, _len = pathsToDrop.length; _i < _len; _i++) {
          p = pathsToDrop[_i];
          delete this.path[p];
        }
        this.traverseSubTree(node, path);
        if (pathInfo.node === this.pathStartNode) {
          console.log("Ended up rescanning the whole doc.");
          this.collectPositions(node, path, null, 0, 0);
        } else {
          parentPath = this.parentPath(path);
          parentPathInfo = this.path[parentPath];
          if (parentPathInfo == null) {
            throw new Error("While performing update on node " + path + ", no path info found for parent path: " + parentPath);
          }
          oldIndex = node === node.parentNode.firstChild ? 0 : this.path[this.getPathTo(node.previousSibling)].end - parentPathInfo.start;
          this.collectPositions(node, path, parentPathInfo.content, parentPathInfo.start, oldIndex);
        }
      } else {
        if (pathInfo.node !== this.pathStartNode) {
          parentNode = node.parentNode != null ? node.parentNode : (parentPath = this.parentPath(path), this.lookUpNode(parentPath));
          this.performUpdateOnNode(parentNode, true);
        } else {
          throw new Error("Can not keep up with the changes, since even the node configured as path start node was replaced.");
        }
      }
      if (!escalating) return this.restoreSelection();
    };

    DomTextMapper.prototype.getInfoForPath = function(path) {
      var result;
      if (this.path == null) {
        throw new Error("Can't get info before running a scan() !");
      }
      result = this.path[path];
      if (result == null) {
        throw new Error("Found no info for path '" + path + "'!");
      }
      return result;
    };

    DomTextMapper.prototype.getInfoForNode = function(node) {
      if (node == null) {
        throw new Error("Called getInfoForNode(node) with null node!");
      }
      return this.getInfoForPath(this.getPathTo(node));
    };

    DomTextMapper.prototype.getMappingsForCharRanges = function(charRanges) {
      var charRange, mapping, _i, _len, _results;
      _results = [];
      for (_i = 0, _len = charRanges.length; _i < _len; _i++) {
        charRange = charRanges[_i];
        _results.push(mapping = this.getMappingsForCharRange(charRange.start, charRange.end));
      }
      return _results;
    };

    DomTextMapper.prototype.getContentForPath = function(path) {
      if (path == null) path = null;
      if (path == null) path = this.getDefaultPath();
      return this.path[path].content;
    };

    DomTextMapper.prototype.getLengthForPath = function(path) {
      if (path == null) path = null;
      if (path == null) path = this.getDefaultPath();
      return this.path[path].length;
    };

    DomTextMapper.prototype.getDocLength = function() {
      return this.getLengthForPath();
    };

    DomTextMapper.prototype.getContentForCharRange = function(start, end, path) {
      var text;
      if (path == null) path = null;
      text = this.getContentForPath(path).substr(start, end - start);
      return text.trim();
    };

    DomTextMapper.prototype.getContextForCharRange = function(start, end, path) {
      var content, prefix, prefixLen, prefixStart, suffix;
      if (path == null) path = null;
      content = this.getContentForPath(path);
      prefixStart = Math.max(0, start - CONTEXT_LEN);
      prefixLen = start - prefixStart;
      prefix = content.substr(prefixStart, prefixLen);
      suffix = content.substr(end, prefixLen);
      return [prefix.trim(), suffix.trim()];
    };

    DomTextMapper.prototype.getMappingsForCharRange = function(start, end) {
      var endInfo, endMapping, endNode, endOffset, endPath, info, mappings, p, r, result, startInfo, startMapping, startNode, startOffset, startPath, _ref,
        _this = this;
      if (!((start != null) && (end != null))) {
        throw new Error("start and end is required!");
      }
      this.scan();
      mappings = [];
      _ref = this.path;
      for (p in _ref) {
        info = _ref[p];
        if (info.atomic && this.regions_overlap(info.start, info.end, start, end)) {
          (function(info) {
            var full, mapping;
            mapping = {
              element: info
            };
            full = start <= info.start && info.end <= end;
            if (full) {
              mapping.full = true;
              mapping.wanted = info.content;
              mapping.yields = info.content;
              mapping.startCorrected = 0;
              mapping.endCorrected = 0;
            } else {
              if (info.node.nodeType === Node.TEXT_NODE) {
                if (start <= info.start) {
                  mapping.end = end - info.start;
                  mapping.wanted = info.content.substr(0, mapping.end);
                } else if (info.end <= end) {
                  mapping.start = start - info.start;
                  mapping.wanted = info.content.substr(mapping.start);
                } else {
                  mapping.start = start - info.start;
                  mapping.end = end - info.start;
                  mapping.wanted = info.content.substr(mapping.start, mapping.end - mapping.start);
                }
                _this.computeSourcePositions(mapping);
                mapping.yields = info.node.data.substr(mapping.startCorrected, mapping.endCorrected - mapping.startCorrected);
              } else if ((info.node.nodeType === Node.ELEMENT_NODE) && (info.node.tagName.toLowerCase() === "img")) {
                console.log("Can not select a sub-string from the title of an image. Selecting all.");
                mapping.full = true;
                mapping.wanted = info.content;
              } else {
                console.log("Warning: no idea how to handle partial mappings for node type " + info.node.nodeType);
                if (info.node.tagName != null) {
                  console.log("Tag: " + info.node.tagName);
                }
                console.log("Selecting all.");
                mapping.full = true;
                mapping.wanted = info.content;
              }
            }
            return mappings.push(mapping);
          })(info);
        }
      }
      if (mappings.length === 0) {
        throw new Error("No mappings found for [" + start + ":" + end + "]!");
      }
      r = this.rootWin.document.createRange();
      startMapping = mappings[0];
      startNode = startMapping.element.node;
      startPath = startMapping.element.path;
      startOffset = startMapping.startCorrected;
      if (startMapping.full) {
        r.setStartBefore(startNode);
        startInfo = startPath;
      } else {
        r.setStart(startNode, startOffset);
        startInfo = startPath + ":" + startOffset;
      }
      endMapping = mappings[mappings.length - 1];
      endNode = endMapping.element.node;
      endPath = endMapping.element.path;
      endOffset = endMapping.endCorrected;
      if (endMapping.full) {
        r.setEndAfter(endNode);
        endInfo = endPath;
      } else {
        r.setEnd(endNode, endOffset);
        endInfo = endPath + ":" + endOffset;
      }
      result = {
        mappings: mappings,
        realRange: r,
        rangeInfo: {
          startPath: startPath,
          startOffset: startOffset,
          startInfo: startInfo,
          endPath: endPath,
          endOffset: endOffset,
          endInfo: endInfo
        },
        safeParent: r.commonAncestorContainer
      };
      return result;
    };

    DomTextMapper.prototype.timestamp = function() {
      return new Date().getTime();
    };

    DomTextMapper.prototype.stringStartsWith = function(string, prefix) {
      return prefix === string.substr(0, prefix.length);
    };

    DomTextMapper.prototype.stringEndsWith = function(string, suffix) {
      return suffix === string.substr(string.length - suffix.length);
    };

    DomTextMapper.prototype.parentPath = function(path) {
      return path.substr(0, path.lastIndexOf("/"));
    };

    DomTextMapper.prototype.domChangedSince = function(timestamp) {
      if ((this.lastDOMChange != null) && (timestamp != null)) {
        return this.lastDOMChange > timestamp;
      } else {
        return true;
      }
    };

    DomTextMapper.prototype.domStableSince = function(timestamp) {
      return !this.domChangedSince(timestamp);
    };

    DomTextMapper.prototype.getProperNodeName = function(node) {
      var nodeName;
      nodeName = node.nodeName;
      switch (nodeName) {
        case "#text":
          return "text()";
        case "#comment":
          return "comment()";
        case "#cdata-section":
          return "cdata-section()";
        default:
          return nodeName;
      }
    };

    DomTextMapper.prototype.getNodePosition = function(node) {
      var pos, tmp;
      pos = 0;
      tmp = node;
      while (tmp) {
        if (tmp.nodeName === node.nodeName) pos++;
        tmp = tmp.previousSibling;
      }
      return pos;
    };

    DomTextMapper.prototype.getPathSegment = function(node) {
      var name, pos;
      name = this.getProperNodeName(node);
      pos = this.getNodePosition(node);
      return name + (pos > 1 ? "[" + pos + "]" : "");
    };

    DomTextMapper.prototype.getPathTo = function(node) {
      var xpath;
      xpath = '';
      while (node !== this.rootNode) {
        if (node == null) {
          throw new Error("Called getPathTo on a node which was not a descendant of @rootNode. " + this.rootNode);
        }
        xpath = (this.getPathSegment(node)) + '/' + xpath;
        node = node.parentNode;
      }
      xpath = (this.rootNode.ownerDocument != null ? './' : '/') + xpath;
      xpath = xpath.replace(/\/$/, '');
      return xpath;
    };

    DomTextMapper.prototype.traverseSubTree = function(node, path, invisible, verbose) {
      var child, cont, subpath, _i, _len, _ref;
      if (invisible == null) invisible = false;
      if (verbose == null) verbose = false;
      this.underTraverse = path;
      cont = this.getNodeContent(node, false);
      this.path[path] = {
        path: path,
        content: cont,
        length: cont.length,
        node: node
      };
      if (cont.length) {
        if (verbose) console.log("Collected info about path " + path);
        if (invisible) {
          console.log("Something seems to be wrong. I see visible content @ " + path + ", while some of the ancestor nodes reported empty contents. Probably a new selection API bug....");
        }
      } else {
        if (verbose) console.log("Found no content at path " + path);
        invisible = true;
      }
      if (node.hasChildNodes()) {
        _ref = node.childNodes;
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          child = _ref[_i];
          subpath = path + '/' + (this.getPathSegment(child));
          this.traverseSubTree(child, subpath, invisible, verbose);
        }
      }
      return null;
    };

    DomTextMapper.prototype.getBody = function() {
      return (this.rootWin.document.getElementsByTagName("body"))[0];
    };

    DomTextMapper.prototype.regions_overlap = function(start1, end1, start2, end2) {
      return start1 < end2 && start2 < end1;
    };

    DomTextMapper.prototype.lookUpNode = function(path) {
      var doc, node, results, _ref;
      doc = (_ref = this.rootNode.ownerDocument) != null ? _ref : this.rootNode;
      results = doc.evaluate(path, this.rootNode, null, 0, null);
      return node = results.iterateNext();
    };

    DomTextMapper.prototype.saveSelection = function() {
      var i, sel, _ref;
      if (this.savedSelection != null) {
        console.log("Selection saved at:");
        console.log(this.selectionSaved);
        throw new Error("Selection already saved!");
      }
      sel = this.rootWin.getSelection();
      for (i = 0, _ref = sel.rangeCount; 0 <= _ref ? i < _ref : i > _ref; 0 <= _ref ? i++ : i--) {
        this.savedSelection = sel.getRangeAt(i);
      }
      switch (sel.rangeCount) {
        case 0:
          if (this.savedSelection == null) this.savedSelection = [];
          break;
        case 1:
          this.savedSelection = [this.savedSelection];
      }
      try {
        throw new Error("Selection was saved here");
      } catch (exception) {
        return this.selectionSaved = exception.stack;
      }
    };

    DomTextMapper.prototype.restoreSelection = function() {
      var range, sel, _i, _len, _ref;
      if (this.savedSelection == null) throw new Error("No selection to restore.");
      sel = this.rootWin.getSelection();
      sel.removeAllRanges();
      _ref = this.savedSelection;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        range = _ref[_i];
        sel.addRange(range);
      }
      return delete this.savedSelection;
    };

    DomTextMapper.prototype.selectNode = function(node, scroll) {
      var children, realRange, sel, sn, _ref;
      if (scroll == null) scroll = false;
      if (node == null) throw new Error("Called selectNode with null node!");
      sel = this.rootWin.getSelection();
      sel.removeAllRanges();
      realRange = this.rootWin.document.createRange();
      if (node.nodeType === Node.ELEMENT_NODE && node.hasChildNodes() && (_ref = node.tagName.toLowerCase(), __indexOf.call(SELECT_CHILDREN_INSTEAD, _ref) >= 0)) {
        children = node.childNodes;
        realRange.setStartBefore(children[0]);
        realRange.setEndAfter(children[children.length - 1]);
        sel.addRange(realRange);
      } else {
        if (USE_TABLE_TEXT_WORKAROUND && node.nodeType === Node.TEXT_NODE && node.parentNode.tagName.toLowerCase() === "table") {} else {
          try {
            realRange.setStartBefore(node);
            realRange.setEndAfter(node);
            sel.addRange(realRange);
          } catch (exception) {
            if (!(USE_EMPTY_TEXT_WORKAROUND && this.isWhitespace(node))) {
              console.log("Warning: failed to scan element @ " + this.underTraverse);
              console.log("Content is: " + node.innerHTML);
              console.log("We won't be able to properly anchor to any text inside this element.");
            }
          }
        }
      }
      if (scroll) {
        sn = node;
        while ((sn != null) && !(sn.scrollIntoViewIfNeeded != null)) {
          sn = sn.parentNode;
        }
        if (sn != null) {
          sn.scrollIntoViewIfNeeded();
        } else {
          console.log("Failed to scroll to element. (Browser does not support scrollIntoViewIfNeeded?)");
        }
      }
      return sel;
    };

    DomTextMapper.prototype.readSelectionText = function(sel) {
      sel || (sel = this.rootWin.getSelection());
      return sel.toString().trim().replace(/\n/g, " ").replace(/\s{2,}/g, " ");
    };

    DomTextMapper.prototype.getNodeSelectionText = function(node, shouldRestoreSelection) {
      var sel, text;
      if (shouldRestoreSelection == null) shouldRestoreSelection = true;
      if (shouldRestoreSelection) this.saveSelection();
      sel = this.selectNode(node);
      text = this.readSelectionText(sel);
      if (shouldRestoreSelection) this.restoreSelection();
      return text;
    };

    DomTextMapper.prototype.computeSourcePositions = function(match) {
      var dc, displayEnd, displayIndex, displayStart, displayText, sc, sourceEnd, sourceIndex, sourceStart, sourceText;
      sourceText = match.element.node.data.replace(/\n/g, " ");
      displayText = match.element.content;
      displayStart = match.start != null ? match.start : 0;
      displayEnd = match.end != null ? match.end : displayText.length;
      if (displayEnd === 0) {
        match.startCorrected = 0;
        match.endCorrected = 0;
        return;
      }
      sourceIndex = 0;
      displayIndex = 0;
      while (!((sourceStart != null) && (sourceEnd != null))) {
        sc = sourceText[sourceIndex];
        dc = displayText[displayIndex];
        if (sc === dc) {
          if (displayIndex === displayStart) sourceStart = sourceIndex;
          displayIndex++;
          if (displayIndex === displayEnd) sourceEnd = sourceIndex + 1;
        }
        sourceIndex++;
      }
      match.startCorrected = sourceStart;
      match.endCorrected = sourceEnd;
      return null;
    };

    DomTextMapper.prototype.getNodeContent = function(node, shouldRestoreSelection) {
      if (shouldRestoreSelection == null) shouldRestoreSelection = true;
      return this.getNodeSelectionText(node, shouldRestoreSelection);
    };

    DomTextMapper.prototype.collectPositions = function(node, path, parentContent, parentIndex, index) {
      var atomic, child, childPath, children, content, endIndex, i, newCount, nodeName, oldCount, pathInfo, pos, startIndex, typeCount;
      if (parentContent == null) parentContent = null;
      if (parentIndex == null) parentIndex = 0;
      if (index == null) index = 0;
      pathInfo = this.path[path];
      content = pathInfo != null ? pathInfo.content : void 0;
      if (!(content != null) || content === "") {
        pathInfo.start = parentIndex + index;
        pathInfo.end = parentIndex + index;
        pathInfo.atomic = false;
        return index;
      }
      startIndex = parentContent != null ? parentContent.indexOf(content, index) : index;
      if (startIndex === -1) return index;
      endIndex = startIndex + content.length;
      atomic = !node.hasChildNodes();
      pathInfo.start = parentIndex + startIndex;
      pathInfo.end = parentIndex + endIndex;
      pathInfo.atomic = atomic;
      if (!atomic) {
        children = node.childNodes;
        i = 0;
        pos = 0;
        typeCount = Object();
        while (i < children.length) {
          child = children[i];
          nodeName = this.getProperNodeName(child);
          oldCount = typeCount[nodeName];
          newCount = oldCount != null ? oldCount + 1 : 1;
          typeCount[nodeName] = newCount;
          childPath = path + "/" + nodeName + (newCount > 1 ? "[" + newCount + "]" : "");
          pos = this.collectPositions(child, childPath, content, parentIndex + startIndex, pos);
          i++;
        }
      }
      return endIndex;
    };

    WHITESPACE = /^\s*$/;

    DomTextMapper.prototype.isWhitespace = function(node) {
      var child, mightBeEmpty, result;
      result = (function() {
        var _i, _len, _ref;
        switch (node.nodeType) {
          case Node.TEXT_NODE:
            return WHITESPACE.test(node.data);
          case Node.ELEMENT_NODE:
            mightBeEmpty = true;
            _ref = node.childNodes;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
              child = _ref[_i];
              mightBeEmpty = mightBeEmpty && this.isWhitespace(child);
            }
            return mightBeEmpty;
          default:
            return false;
        }
      }).call(this);
      return result;
    };

    return DomTextMapper;

  })();

  window.DTM_ExactMatcher = (function() {

    function DTM_ExactMatcher() {
      this.distinct = true;
      this.caseSensitive = false;
    }

    DTM_ExactMatcher.prototype.setDistinct = function(value) {
      return this.distinct = value;
    };

    DTM_ExactMatcher.prototype.setCaseSensitive = function(value) {
      return this.caseSensitive = value;
    };

    DTM_ExactMatcher.prototype.search = function(text, pattern) {
      var i, index, pLen, results,
        _this = this;
      pLen = pattern.length;
      results = [];
      index = 0;
      if (!this.caseSensitive) {
        text = text.toLowerCase();
        pattern = pattern.toLowerCase();
      }
      while ((i = text.indexOf(pattern)) > -1) {
        (function() {
          results.push({
            start: index + i,
            end: index + i + pLen
          });
          if (_this.distinct) {
            text = text.substr(i + pLen);
            return index += i + pLen;
          } else {
            text = text.substr(i + 1);
            return index += i + 1;
          }
        })();
      }
      return results;
    };

    return DTM_ExactMatcher;

  })();

  window.DTM_RegexMatcher = (function() {

    function DTM_RegexMatcher() {
      this.caseSensitive = false;
    }

    DTM_RegexMatcher.prototype.setCaseSensitive = function(value) {
      return this.caseSensitive = value;
    };

    DTM_RegexMatcher.prototype.search = function(text, pattern) {
      var m, re, _results;
      re = new RegExp(pattern, this.caseSensitive ? "g" : "gi");
      _results = [];
      while (m = re.exec(text)) {
        _results.push({
          start: m.index,
          end: m.index + m[0].length
        });
      }
      return _results;
    };

    return DTM_RegexMatcher;

  })();

  window.DTM_DMPMatcher = (function() {

    function DTM_DMPMatcher() {
      this.dmp = new diff_match_patch;
      this.dmp.Diff_Timeout = 0;
      this.caseSensitive = false;
    }

    DTM_DMPMatcher.prototype._reverse = function(text) {
      return text.split("").reverse().join("");
    };

    DTM_DMPMatcher.prototype.getMaxPatternLength = function() {
      return this.dmp.Match_MaxBits;
    };

    DTM_DMPMatcher.prototype.setMatchDistance = function(distance) {
      return this.dmp.Match_Distance = distance;
    };

    DTM_DMPMatcher.prototype.getMatchDistance = function() {
      return this.dmp.Match_Distance;
    };

    DTM_DMPMatcher.prototype.setMatchThreshold = function(threshold) {
      return this.dmp.Match_Threshold = threshold;
    };

    DTM_DMPMatcher.prototype.getMatchThreshold = function() {
      return this.dmp.Match_Threshold;
    };

    DTM_DMPMatcher.prototype.getCaseSensitive = function() {
      return caseSensitive;
    };

    DTM_DMPMatcher.prototype.setCaseSensitive = function(value) {
      return this.caseSensitive = value;
    };

    DTM_DMPMatcher.prototype.search = function(text, pattern, expectedStartLoc, options) {
      var endIndex, endLen, endLoc, endPos, endSlice, found, matchLen, maxLen, pLen, result, startIndex, startLen, startPos, startSlice;
      if (expectedStartLoc == null) expectedStartLoc = 0;
      if (options == null) options = {};
      if (expectedStartLoc < 0) {
        throw new Error("Can't search at negative indices!");
      }
      if (!this.caseSensitive) {
        text = text.toLowerCase();
        pattern = pattern.toLowerCase();
      }
      pLen = pattern.length;
      maxLen = this.getMaxPatternLength();
      if (pLen <= maxLen) {
        result = this.searchForSlice(text, pattern, expectedStartLoc);
      } else {
        startSlice = pattern.substr(0, maxLen);
        startPos = this.searchForSlice(text, startSlice, expectedStartLoc);
        if (startPos != null) {
          startLen = startPos.end - startPos.start;
          endSlice = pattern.substr(pLen - maxLen, maxLen);
          endLoc = startPos.start + pLen - maxLen;
          endPos = this.searchForSlice(text, endSlice, endLoc);
          if (endPos != null) {
            endLen = endPos.end - endPos.start;
            matchLen = endPos.end - startPos.start;
            startIndex = startPos.start;
            endIndex = endPos.end;
            if ((pLen * 0.5 <= matchLen && matchLen <= pLen * 1.5)) {
              result = {
                start: startIndex,
                end: endPos.end
              };
            }
          }
        }
      }
      if (result == null) return [];
      if (options.withLevenhstein || options.withDiff) {
        found = text.substr(result.start, result.end - result.start);
        result.diff = this.dmp.diff_main(pattern, found);
        if (options.withLevenshstein) {
          result.lev = this.dmp.diff_levenshtein(result.diff);
        }
        if (options.withDiff) {
          this.dmp.diff_cleanupSemantic(result.diff);
          result.diffHTML = this.dmp.diff_prettyHtml(result.diff);
        }
      }
      return [result];
    };

    DTM_DMPMatcher.prototype.compare = function(text1, text2) {
      var result;
      if (!((text1 != null) && (text2 != null))) {
        throw new Error("Can not compare non-existing strings!");
      }
      result = {};
      result.diff = this.dmp.diff_main(text1, text2);
      result.lev = this.dmp.diff_levenshtein(result.diff);
      result.errorLevel = result.lev / text1.length;
      this.dmp.diff_cleanupSemantic(result.diff);
      result.diffHTML = this.dmp.diff_prettyHtml(result.diff);
      return result;
    };

    DTM_DMPMatcher.prototype.searchForSlice = function(text, slice, expectedStartLoc) {
      var dneIndex, endIndex, expectedDneLoc, expectedEndLoc, nrettap, r1, r2, result, startIndex, txet;
      r1 = this.dmp.match_main(text, slice, expectedStartLoc);
      startIndex = r1.index;
      if (startIndex === -1) return null;
      txet = this._reverse(text);
      nrettap = this._reverse(slice);
      expectedEndLoc = startIndex + slice.length;
      expectedDneLoc = text.length - expectedEndLoc;
      r2 = this.dmp.match_main(txet, nrettap, expectedDneLoc);
      dneIndex = r2.index;
      endIndex = text.length - dneIndex;
      return result = {
        start: startIndex,
        end: endIndex
      };
    };

    return DTM_DMPMatcher;

  })();

  window.DomTextMatcher = (function() {

    DomTextMatcher.prototype.setRootNode = function(rootNode) {
      return this.mapper.setRootNode(rootNode);
    };

    DomTextMatcher.prototype.setRootId = function(rootId) {
      return this.mapper.setRootId(rootId);
    };

    DomTextMatcher.prototype.setRootIframe = function(iframeId) {
      return this.mapper.setRootIframe(iframeId);
    };

    DomTextMatcher.prototype.setRealRoot = function() {
      return this.mapper.setRealRoot();
    };

    DomTextMatcher.prototype.documentChanged = function() {
      return this.mapper.documentChanged();
    };

    DomTextMatcher.prototype.scan = function() {
      var data, t0, t1;
      t0 = this.timestamp();
      data = this.mapper.scan();
      t1 = this.timestamp();
      return {
        time: t1 - t0,
        data: data
      };
    };

    DomTextMatcher.prototype.getDefaultPath = function() {
      return this.mapper.getDefaultPath();
    };

    DomTextMatcher.prototype.searchExact = function(pattern, distinct, caseSensitive, path) {
      if (distinct == null) distinct = true;
      if (caseSensitive == null) caseSensitive = false;
      if (path == null) path = null;
      if (!this.pm) this.pm = new window.DTM_ExactMatcher;
      this.pm.setDistinct(distinct);
      this.pm.setCaseSensitive(caseSensitive);
      return this.search(this.pm, pattern, null, path);
    };

    DomTextMatcher.prototype.searchRegex = function(pattern, caseSensitive, path) {
      if (caseSensitive == null) caseSensitive = false;
      if (path == null) path = null;
      if (!this.rm) this.rm = new window.DTM_RegexMatcher;
      this.rm.setCaseSensitive(caseSensitive);
      return this.search(this.rm, pattern, null, path);
    };

    DomTextMatcher.prototype.searchFuzzy = function(pattern, pos, caseSensitive, path, options) {
      var _ref, _ref2;
      if (caseSensitive == null) caseSensitive = false;
      if (path == null) path = null;
      if (options == null) options = {};
      this.ensureDMP();
      this.dmp.setMatchDistance((_ref = options.matchDistance) != null ? _ref : 1000);
      this.dmp.setMatchThreshold((_ref2 = options.matchThreshold) != null ? _ref2 : 0.5);
      this.dmp.setCaseSensitive(caseSensitive);
      return this.search(this.dmp, pattern, pos, path, options);
    };

    DomTextMatcher.prototype.normalizeString = function(string) {
      return string.replace(/\s{2,}/g, " ");
    };

    DomTextMatcher.prototype.searchFuzzyWithContext = function(prefix, suffix, pattern, expectedStart, expectedEnd, caseSensitive, path, options) {
      var analysis, charRange, expectedPrefixStart, expectedSuffixStart, k, len, mappings, match, matchThreshold, obj, patternLength, prefixEnd, prefixResult, remainingText, suffixResult, suffixStart, v, _i, _len, _ref, _ref2, _ref3, _ref4;
      if (expectedStart == null) expectedStart = null;
      if (expectedEnd == null) expectedEnd = null;
      if (caseSensitive == null) caseSensitive = false;
      if (path == null) path = null;
      if (options == null) options = {};
      this.ensureDMP();
      if (!((prefix != null) && (suffix != null))) {
        throw new Error("Can not do a context-based fuzzy search with missing context!");
      }
      len = this.mapper.getDocLength();
      expectedPrefixStart = expectedStart != null ? expectedStart - prefix.length : len / 2;
      this.dmp.setMatchDistance((_ref = options.contextMatchDistance) != null ? _ref : len * 2);
      this.dmp.setMatchThreshold((_ref2 = options.contextMatchThreshold) != null ? _ref2 : 0.5);
      prefixResult = this.dmp.search(this.mapper.corpus, prefix, expectedPrefixStart);
      if (!prefixResult.length) {
        return {
          matches: []
        };
      }
      prefixEnd = prefixResult[0].end;
      patternLength = pattern != null ? pattern.length : (expectedStart != null) && (expectedEnd != null) ? expectedEnd - expectedStart : 64;
      remainingText = this.mapper.corpus.substr(prefixEnd);
      expectedSuffixStart = patternLength;
      suffixResult = this.dmp.search(remainingText, suffix, expectedSuffixStart);
      if (!suffixResult.length) {
        return {
          matches: []
        };
      }
      suffixStart = prefixEnd + suffixResult[0].start;
      charRange = {
        start: prefixEnd,
        end: suffixStart
      };
      matchThreshold = (_ref3 = options.patternMatchThreshold) != null ? _ref3 : 0.5;
      analysis = this.analyzeMatch(pattern, charRange, true);
      if ((!(pattern != null)) || analysis.exact || (analysis.comparison.errorLevel <= matchThreshold)) {
        mappings = this.mapper.getMappingsForCharRange(prefixEnd, suffixStart);
        match = {};
        _ref4 = [charRange, analysis, mappings];
        for (_i = 0, _len = _ref4.length; _i < _len; _i++) {
          obj = _ref4[_i];
          for (k in obj) {
            v = obj[k];
            match[k] = v;
          }
        }
        return {
          matches: [match]
        };
      }
      return {
        matches: []
      };
    };

    function DomTextMatcher(domTextMapper) {
      this.mapper = domTextMapper;
    }

    DomTextMatcher.prototype.search = function(matcher, pattern, pos, path, options) {
      var fuzzyComparison, matches, result, t0, t1, t2, t3, textMatch, textMatches, _fn, _i, _len, _ref,
        _this = this;
      if (path == null) path = null;
      if (options == null) options = {};
      if (pattern == null) throw new Error("Can't search for null pattern!");
      pattern = pattern.trim();
      if (pattern == null) throw new Error("Can't search an for empty pattern!");
      fuzzyComparison = (_ref = options.withFuzzyComparison) != null ? _ref : false;
      t0 = this.timestamp();
      if (path != null) this.scan();
      t1 = this.timestamp();
      textMatches = matcher.search(this.mapper.corpus, pattern, pos, options);
      t2 = this.timestamp();
      matches = [];
      _fn = function(textMatch) {
        var analysis, k, mappings, match, obj, v, _j, _len2, _ref2;
        analysis = _this.analyzeMatch(pattern, textMatch, fuzzyComparison);
        mappings = _this.mapper.getMappingsForCharRange(textMatch.start, textMatch.end);
        match = {};
        _ref2 = [textMatch, analysis, mappings];
        for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
          obj = _ref2[_j];
          for (k in obj) {
            v = obj[k];
            match[k] = v;
          }
        }
        matches.push(match);
        return null;
      };
      for (_i = 0, _len = textMatches.length; _i < _len; _i++) {
        textMatch = textMatches[_i];
        _fn(textMatch);
      }
      t3 = this.timestamp();
      result = {
        matches: matches,
        time: {
          phase0_domMapping: t1 - t0,
          phase1_textMatching: t2 - t1,
          phase2_matchMapping: t3 - t2,
          total: t3 - t0
        }
      };
      return result;
    };

    DomTextMatcher.prototype.timestamp = function() {
      return new Date().getTime();
    };

    DomTextMatcher.prototype.analyzeMatch = function(pattern, charRange, useFuzzy) {
      var expected, found, result;
      if (useFuzzy == null) useFuzzy = false;
      expected = this.normalizeString(pattern);
      found = this.normalizeString(this.mapper.getContentForCharRange(charRange.start, charRange.end));
      result = {
        found: found,
        exact: found === expected
      };
      if (!result.exact && useFuzzy) {
        this.ensureDMP();
        result.comparison = this.dmp.compare(expected, found);
      }
      return result;
    };

    DomTextMatcher.prototype.ensureDMP = function() {
      if (this.dmp == null) {
        if (window.DTM_DMPMatcher == null) {
          throw new Error("DTM_DMPMatcher is not available. Have you loaded the text match engines?");
        }
        return this.dmp = new window.DTM_DMPMatcher;
      }
    };

    return DomTextMatcher;

  })();

  gettext = null;

  if (typeof Gettext !== "undefined" && Gettext !== null) {
    _gettext = new Gettext({
      domain: "annotator"
    });
    gettext = function(msgid) {
      return _gettext.gettext(msgid);
    };
  } else {
    gettext = function(msgid) {
      return msgid;
    };
  }

  _t = function(msgid) {
    return gettext(msgid);
  };

  if (!(typeof jQuery !== "undefined" && jQuery !== null ? (_ref = jQuery.fn) != null ? _ref.jquery : void 0 : void 0)) {
    console.error(_t("Annotator requires jQuery: have you included lib/vendor/jquery.js?"));
  }

  if (!(JSON && JSON.parse && JSON.stringify)) {
    console.error(_t("Annotator requires a JSON implementation: have you included lib/vendor/json2.js?"));
  }

  $ = jQuery.sub();

  $.flatten = function(array) {
    var flatten;
    flatten = function(ary) {
      var el, flat, _i, _len;
      flat = [];
      for (_i = 0, _len = ary.length; _i < _len; _i++) {
        el = ary[_i];
        flat = flat.concat(el && $.isArray(el) ? flatten(el) : el);
      }
      return flat;
    };
    return flatten(array);
  };

  $.plugin = function(name, object) {
    return jQuery.fn[name] = function(options) {
      var args;
      args = Array.prototype.slice.call(arguments, 1);
      return this.each(function() {
        var instance;
        instance = $.data(this, name);
        if (instance) {
          return options && instance[options].apply(instance, args);
        } else {
          instance = new object(this, options);
          return $.data(this, name, instance);
        }
      });
    };
  };

  $.fn.textNodes = function() {
    var getTextNodes;
    getTextNodes = function(node) {
      var nodes;
      if (node && node.nodeType !== 3) {
        nodes = [];
        if (node.nodeType !== 8) {
          node = node.lastChild;
          while (node) {
            nodes.push(getTextNodes(node));
            node = node.previousSibling;
          }
        }
        return nodes.reverse();
      } else {
        return node;
      }
    };
    return this.map(function() {
      return $.flatten(getTextNodes(this));
    });
  };

  $.fn.xpath = function(relativeRoot) {
    var jq;
    jq = this.map(function() {
      var elem, idx, path;
      path = '';
      elem = this;
      while (elem && elem.nodeType === 1 && elem !== relativeRoot) {
        idx = $(elem.parentNode).children(elem.tagName).index(elem) + 1;
        idx = "[" + idx + "]";
        path = "/" + elem.tagName.toLowerCase() + idx + path;
        elem = elem.parentNode;
      }
      return path;
    });
    return jq.get();
  };

  $.escape = function(html) {
    return html.replace(/&(?!\w+;)/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  };

  $.fn.escape = function(html) {
    if (arguments.length) return this.html($.escape(html));
    return this.html();
  };

  $.fn.reverse = []._reverse || [].reverse;

  functions = ["log", "debug", "info", "warn", "exception", "assert", "dir", "dirxml", "trace", "group", "groupEnd", "groupCollapsed", "time", "timeEnd", "profile", "profileEnd", "count", "clear", "table", "error", "notifyFirebug", "firebug", "userObjects"];

  if (typeof console !== "undefined" && console !== null) {
    if (!(console.group != null)) {
      console.group = function(name) {
        return console.log("GROUP: ", name);
      };
    }
    if (!(console.groupCollapsed != null)) console.groupCollapsed = console.group;
    for (_i = 0, _len = functions.length; _i < _len; _i++) {
      fn = functions[_i];
      if (!(console[fn] != null)) {
        console[fn] = function() {
          return console.log(_t("Not implemented:") + (" console." + name));
        };
      }
    }
  } else {
    this.console = {};
    for (_j = 0, _len2 = functions.length; _j < _len2; _j++) {
      fn = functions[_j];
      this.console[fn] = function() {};
    }
    this.console['error'] = function() {
      var args;
      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      return alert("ERROR: " + (args.join(', ')));
    };
    this.console['warn'] = function() {
      var args;
      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      return alert("WARNING: " + (args.join(', ')));
    };
  }

  Delegator = (function() {

    Delegator.prototype.events = {};

    Delegator.prototype.options = {};

    Delegator.prototype.element = null;

    function Delegator(element, options) {
      this.options = $.extend(true, {}, this.options, options);
      this.element = $(element);
      this.on = this.subscribe;
      this.addEvents();
    }

    Delegator.prototype.addEvents = function() {
      var event, functionName, sel, selector, _k, _ref2, _ref3, _results;
      _ref2 = this.events;
      _results = [];
      for (sel in _ref2) {
        functionName = _ref2[sel];
        _ref3 = sel.split(' '), selector = 2 <= _ref3.length ? __slice.call(_ref3, 0, _k = _ref3.length - 1) : (_k = 0, []), event = _ref3[_k++];
        _results.push(this.addEvent(selector.join(' '), event, functionName));
      }
      return _results;
    };

    Delegator.prototype.addEvent = function(bindTo, event, functionName) {
      var closure, isBlankSelector,
        _this = this;
      closure = function() {
        return _this[functionName].apply(_this, arguments);
      };
      isBlankSelector = typeof bindTo === 'string' && bindTo.replace(/\s+/g, '') === '';
      if (isBlankSelector) bindTo = this.element;
      if (typeof bindTo === 'string') {
        this.element.delegate(bindTo, event, closure);
      } else {
        if (this.isCustomEvent(event)) {
          this.subscribe(event, closure);
        } else {
          $(bindTo).bind(event, closure);
        }
      }
      return this;
    };

    Delegator.prototype.isCustomEvent = function(event) {
      event = event.split('.')[0];
      return $.inArray(event, Delegator.natives) === -1;
    };

    Delegator.prototype.publish = function() {
      this.element.triggerHandler.apply(this.element, arguments);
      return this;
    };

    Delegator.prototype.subscribe = function(event, callback) {
      var closure;
      closure = function() {
        return callback.apply(this, [].slice.call(arguments, 1));
      };
      closure.guid = callback.guid = ($.guid += 1);
      this.element.bind(event, closure);
      return this;
    };

    Delegator.prototype.unsubscribe = function() {
      this.element.unbind.apply(this.element, arguments);
      return this;
    };

    return Delegator;

  })();

  Delegator.natives = (function() {
    var key, specials, val;
    specials = (function() {
      var _ref2, _results;
      _ref2 = jQuery.event.special;
      _results = [];
      for (key in _ref2) {
        if (!__hasProp.call(_ref2, key)) continue;
        val = _ref2[key];
        _results.push(key);
      }
      return _results;
    })();
    return "blur focus focusin focusout load resize scroll unload click dblclick\nmousedown mouseup mousemove mouseover mouseout mouseenter mouseleave\nchange select submit keydown keypress keyup error".split(/[^a-z]+/).concat(specials);
  })();

  Range = {};

  Range.sniff = function(r) {
    if (r.commonAncestorContainer != null) {
      return new Range.BrowserRange(r);
    } else if (typeof r.start === "string") {
      return new Range.SerializedRange({
        startContainer: r.start,
        startOffset: r.startOffset,
        endContainer: r.end,
        endOffset: r.endOffset
      });
    } else if (typeof r.startContainer === "string") {
      return new Range.SerializedRange(r);
    } else if (r.start && typeof r.start === "object") {
      return new Range.NormalizedRange(r);
    } else {
      console.error(_t("Could not sniff range type"));
      return false;
    }
  };

  Range.nodeFromXPath = function(xpath, root) {
    var customResolver, evaluateXPath, namespace, node, segment;
    if (root == null) root = document;
    evaluateXPath = function(xp, nsResolver) {
      if (nsResolver == null) nsResolver = null;
      return document.evaluate('.' + xp, root, nsResolver, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    };
    if (!$.isXMLDoc(document.documentElement)) {
      return evaluateXPath(xpath);
    } else {
      customResolver = document.createNSResolver(document.ownerDocument === null ? document.documentElement : document.ownerDocument.documentElement);
      node = evaluateXPath(xpath, customResolver);
      if (!node) {
        xpath = ((function() {
          var _k, _len3, _ref2, _results;
          _ref2 = xpath.split('/');
          _results = [];
          for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
            segment = _ref2[_k];
            if (segment && segment.indexOf(':') === -1) {
              _results.push(segment.replace(/^([a-z]+)/, 'xhtml:$1'));
            } else {
              _results.push(segment);
            }
          }
          return _results;
        })()).join('/');
        namespace = document.lookupNamespaceURI(null);
        customResolver = function(ns) {
          if (ns === 'xhtml') {
            return namespace;
          } else {
            return document.documentElement.getAttribute('xmlns:' + ns);
          }
        };
        node = evaluateXPath(xpath, customResolver);
      }
      return node;
    }
  };

  Range.RangeError = (function(_super) {

    __extends(RangeError, _super);

    function RangeError(type, message, parent) {
      this.type = type;
      this.message = message;
      this.parent = parent != null ? parent : null;
      RangeError.__super__.constructor.call(this, this.message);
    }

    return RangeError;

  })(Error);

  Range.BrowserRange = (function() {

    function BrowserRange(obj) {
      this.commonAncestorContainer = obj.commonAncestorContainer;
      this.startContainer = obj.startContainer;
      this.startOffset = obj.startOffset;
      this.endContainer = obj.endContainer;
      this.endOffset = obj.endOffset;
    }

    BrowserRange.prototype.normalize = function(root) {
      var isImg, it, node, nr, offset, p, r, _k, _len3, _ref2;
      if (this.tainted) {
        console.error(_t("You may only call normalize() once on a BrowserRange!"));
        return false;
      } else {
        this.tainted = true;
      }
      r = {};
      nr = {};
      _ref2 = ['start', 'end'];
      for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
        p = _ref2[_k];
        node = this[p + 'Container'];
        offset = this[p + 'Offset'];
        if (node.nodeType === Node.ELEMENT_NODE) {
          it = node.childNodes[offset];
          node = it || node.childNodes[offset - 1];
          isImg = node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() === "img";
          if (isImg) {
            offset = 0;
          } else {
            while (node.nodeType === Node.ELEMENT_NODE && !node.firstChild && !isImg) {
              it = null;
              node = node.previousSibling;
            }
            while (node.nodeType !== Node.TEXT_NODE) {
              node = node.firstChild;
            }
            offset = it ? 0 : node.nodeValue.length;
          }
        }
        r[p] = node;
        r[p + 'Offset'] = offset;
        r[p + 'Img'] = isImg;
      }
      nr.start = r.startOffset > 0 ? r.start.splitText(r.startOffset) : r.start;
      if (r.start === r.end && !r.startImg) {
        if ((r.endOffset - r.startOffset) < nr.start.nodeValue.length) {
          nr.start.splitText(r.endOffset - r.startOffset);
        }
        nr.end = nr.start;
      } else {
        if (r.endOffset < r.end.nodeValue.length && !r.endImg) {
          r.end.splitText(r.endOffset);
        }
        nr.end = r.end;
      }
      nr.commonAncestor = this.commonAncestorContainer;
      while (nr.commonAncestor.nodeType !== 1) {
        nr.commonAncestor = nr.commonAncestor.parentNode;
      }
      if (window.DomTextMapper != null) {
        window.DomTextMapper.changed(nr.commonAncestor, "range normalization");
      }
      return new Range.NormalizedRange(nr);
    };

    BrowserRange.prototype.serialize = function(root, ignoreSelector) {
      return this.normalize(root).serialize(root, ignoreSelector);
    };

    return BrowserRange;

  })();

  Range.NormalizedRange = (function() {

    function NormalizedRange(obj) {
      this.commonAncestor = obj.commonAncestor;
      this.start = obj.start;
      this.end = obj.end;
    }

    NormalizedRange.prototype.normalize = function(root) {
      return this;
    };

    NormalizedRange.prototype.limit = function(bounds) {
      var nodes, parent, startParents, _k, _len3, _ref2;
      nodes = $.grep(this.textNodes(), function(node) {
        return node.parentNode === bounds || $.contains(bounds, node.parentNode);
      });
      if (!nodes.length) return null;
      this.start = nodes[0];
      this.end = nodes[nodes.length - 1];
      startParents = $(this.start).parents();
      _ref2 = $(this.end).parents();
      for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
        parent = _ref2[_k];
        if (startParents.index(parent) !== -1) {
          this.commonAncestor = parent;
          break;
        }
      }
      return this;
    };

    NormalizedRange.prototype.serialize = function(root, ignoreSelector) {
      var end, serialization, start;
      serialization = function(node, isEnd) {
        var isImg, n, nodes, offset, origParent, textNodes, xpath, _k, _len3;
        if (ignoreSelector) {
          origParent = $(node).parents(":not(" + ignoreSelector + ")").eq(0);
        } else {
          origParent = $(node).parent();
        }
        xpath = origParent.xpath(root)[0];
        textNodes = origParent.textNodes();
        nodes = textNodes.slice(0, textNodes.index(node));
        offset = 0;
        for (_k = 0, _len3 = nodes.length; _k < _len3; _k++) {
          n = nodes[_k];
          offset += n.nodeValue.length;
        }
        isImg = node.nodeType === 1 && node.tagName.toLowerCase() === "img";
        if (isEnd && !isImg) {
          return [xpath, offset + node.nodeValue.length];
        } else {
          return [xpath, offset];
        }
      };
      start = serialization(this.start);
      end = serialization(this.end, true);
      return new Range.SerializedRange({
        startContainer: start[0],
        endContainer: end[0],
        startOffset: start[1],
        endOffset: end[1]
      });
    };

    NormalizedRange.prototype.text = function() {
      var node;
      return ((function() {
        var _k, _len3, _ref2, _results;
        _ref2 = this.textNodes();
        _results = [];
        for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
          node = _ref2[_k];
          _results.push(node.nodeValue);
        }
        return _results;
      }).call(this)).join('');
    };

    NormalizedRange.prototype.textNodes = function() {
      var end, start, textNodes, _ref2;
      textNodes = $(this.commonAncestor).textNodes();
      _ref2 = [textNodes.index(this.start), textNodes.index(this.end)], start = _ref2[0], end = _ref2[1];
      return $.makeArray(textNodes.slice(start, end + 1 || 9e9));
    };

    NormalizedRange.prototype.toRange = function() {
      var range;
      range = document.createRange();
      range.setStartBefore(this.start);
      range.setEndAfter(this.end);
      return range;
    };

    return NormalizedRange;

  })();

  Range.SerializedRange = (function() {

    function SerializedRange(obj) {
      this.startContainer = obj.startContainer;
      this.startOffset = obj.startOffset;
      this.endContainer = obj.endContainer;
      this.endOffset = obj.endOffset;
    }

    SerializedRange.prototype.normalize = function(root) {
      var contains, length, node, p, range, tn, xpath, _k, _l, _len3, _len4, _ref2, _ref3;
      range = {};
      _ref2 = ['start', 'end'];
      for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
        p = _ref2[_k];
        xpath = this[p + 'Container'];
        try {
          node = Range.nodeFromXPath(xpath, root);
        } catch (e) {
          throw new Range.RangeError(p, ("Error while finding " + p + " node: " + xpath + ": ") + e, e);
        }
        if (!node) {
          throw new Range.RangeError(p, "Couldn't find " + p + " node: " + xpath);
        }
        length = 0;
        _ref3 = $(node).textNodes();
        for (_l = 0, _len4 = _ref3.length; _l < _len4; _l++) {
          tn = _ref3[_l];
          if (length + tn.nodeValue.length >= this[p + 'Offset']) {
            range[p + 'Container'] = tn;
            range[p + 'Offset'] = this[p + 'Offset'] - length;
            break;
          } else {
            length += tn.nodeValue.length;
          }
        }
        if (!(range[p + 'Offset'] != null)) {
          throw new Range.RangeError("" + p + "offset", "Couldn't find offset " + this[p + 'Offset'] + " in element " + this[p]);
        }
      }
      contains = !(document.compareDocumentPosition != null) ? function(a, b) {
        return a.contains(b);
      } : function(a, b) {
        return a.compareDocumentPosition(b) & 16;
      };
      $(range.startContainer).parents().each(function() {
        if (contains(this, range.endContainer)) {
          range.commonAncestorContainer = this;
          return false;
        }
      });
      return new Range.BrowserRange(range).normalize(root);
    };

    SerializedRange.prototype.serialize = function(root, ignoreSelector) {
      return this.normalize(root).serialize(root, ignoreSelector);
    };

    SerializedRange.prototype.toObject = function() {
      return {
        startContainer: this.startContainer,
        startOffset: this.startOffset,
        endContainer: this.endContainer,
        endOffset: this.endOffset
      };
    };

    return SerializedRange;

  })();

  util = {
    uuid: (function() {
      var counter;
      counter = 0;
      return function() {
        return counter++;
      };
    })(),
    getGlobal: function() {
      return (function() {
        return this;
      })();
    },
    maxZIndex: function($elements) {
      var all, el;
      all = (function() {
        var _k, _len3, _results;
        _results = [];
        for (_k = 0, _len3 = $elements.length; _k < _len3; _k++) {
          el = $elements[_k];
          if ($(el).css('position') === 'static') {
            _results.push(-1);
          } else {
            _results.push(parseInt($(el).css('z-index'), 10) || -1);
          }
        }
        return _results;
      })();
      return Math.max.apply(Math, all);
    },
    mousePosition: function(e, offsetEl) {
      var offset;
      offset = $(offsetEl).offset();
      return {
        top: e.pageY - offset.top,
        left: e.pageX - offset.left
      };
    },
    preventEventDefault: function(event) {
      return event != null ? typeof event.preventDefault === "function" ? event.preventDefault() : void 0 : void 0;
    }
  };

  _Annotator = this.Annotator;

  Annotator = (function(_super) {

    __extends(Annotator, _super);

    Annotator.prototype.events = {
      ".annotator-adder button click": "onAdderClick",
      ".annotator-adder button mousedown": "onAdderMousedown",
      ".annotator-hl mouseover": "onHighlightMouseover",
      ".annotator-hl mouseout": "startViewerHideTimer"
    };

    Annotator.prototype.html = {
      adder: '<div class="annotator-adder"><button>' + _t('Annotate') + '</button></div>',
      wrapper: '<div class="annotator-wrapper"></div>'
    };

    Annotator.prototype.options = {
      readOnly: false
    };

    Annotator.prototype.plugins = {};

    Annotator.prototype.editor = null;

    Annotator.prototype.viewer = null;

    Annotator.prototype.selectedTargets = null;

    Annotator.prototype.mouseIsDown = false;

    Annotator.prototype.ignoreMouseup = false;

    Annotator.prototype.viewerHideTimer = null;

    function Annotator(element, options) {
      this.onDeleteAnnotation = __bind(this.onDeleteAnnotation, this);
      this.onEditAnnotation = __bind(this.onEditAnnotation, this);
      this.onAdderClick = __bind(this.onAdderClick, this);
      this.onAdderMousedown = __bind(this.onAdderMousedown, this);
      this.onHighlightMouseover = __bind(this.onHighlightMouseover, this);
      this.checkForEndSelection = __bind(this.checkForEndSelection, this);
      this.checkForStartSelection = __bind(this.checkForStartSelection, this);
      this.clearViewerHideTimer = __bind(this.clearViewerHideTimer, this);
      this.startViewerHideTimer = __bind(this.startViewerHideTimer, this);
      this.showViewer = __bind(this.showViewer, this);
      this.onEditorSubmit = __bind(this.onEditorSubmit, this);
      this.onEditorHide = __bind(this.onEditorHide, this);
      this.showEditor = __bind(this.showEditor, this);
      this.getHref = __bind(this.getHref, this);      Annotator.__super__.constructor.apply(this, arguments);
      this.plugins = {};
      if (!Annotator.supported()) return this;
      if (!this.options.readOnly) this._setupDocumentEvents();
      if (!this.options.noMatching) this._setupMatching();
      this._setupWrapper()._setupViewer()._setupEditor();
      this._setupDynamicStyle();
      if (!(this.options.noScan || this.options.noMatching)) this._scan();
      this.adder = $(this.html.adder).appendTo(this.wrapper).hide();
    }

    Annotator.prototype._setupMatching = function() {
      this.domMapper = new DomTextMapper();
      this.domMatcher = new DomTextMatcher(this.domMapper);
      return this;
    };

    Annotator.prototype._scan = function() {
      return this.domMatcher.scan();
    };

    Annotator.prototype._setupWrapper = function() {
      this.wrapper = $(this.html.wrapper);
      this.element.find('script').remove();
      this.element.wrapInner(this.wrapper);
      this.wrapper = this.element.find('.annotator-wrapper');
      this.domMapper.setRootNode(this.wrapper[0]);
      return this;
    };

    Annotator.prototype._setupViewer = function() {
      var _this = this;
      this.viewer = new Annotator.Viewer({
        readOnly: this.options.readOnly
      });
      this.viewer.hide().on("edit", this.onEditAnnotation).on("delete", this.onDeleteAnnotation).addField({
        load: function(field, annotation) {
          if (annotation.text) {
            $(field).escape(annotation.text);
          } else {
            $(field).html("<i>" + (_t('No Comment')) + "</i>");
          }
          return _this.publish('annotationViewerTextField', [field, annotation]);
        }
      }).element.appendTo(this.wrapper).bind({
        "mouseover": this.clearViewerHideTimer,
        "mouseout": this.startViewerHideTimer
      });
      return this;
    };

    Annotator.prototype._setupEditor = function() {
      this.editor = new Annotator.Editor();
      this.editor.hide().on('hide', this.onEditorHide).on('save', this.onEditorSubmit).addField({
        type: 'textarea',
        label: _t('Comments') + '\u2026',
        load: function(field, annotation) {
          return $(field).find('textarea').val(annotation.text || '');
        },
        submit: function(field, annotation) {
          return annotation.text = $(field).find('textarea').val();
        }
      });
      this.editor.element.appendTo(this.wrapper);
      return this;
    };

    Annotator.prototype._setupDocumentEvents = function() {
      $(document).bind({
        "mouseup": this.checkForEndSelection,
        "mousedown": this.checkForStartSelection
      });
      return this;
    };

    Annotator.prototype._setupDynamicStyle = function() {
      var max, sel, style, x;
      style = $('#annotator-dynamic-style');
      if (!style.length) {
        style = $('<style id="annotator-dynamic-style"></style>').appendTo(document.head);
      }
      sel = '*' + ((function() {
        var _k, _len3, _ref2, _results;
        _ref2 = ['adder', 'outer', 'notice', 'filter'];
        _results = [];
        for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
          x = _ref2[_k];
          _results.push(":not(.annotator-" + x + ")");
        }
        return _results;
      })()).join('');
      max = util.maxZIndex($(document.body).find(sel));
      max = Math.max(max, 1000);
      style.text([".annotator-adder, .annotator-outer, .annotator-notice {", "  z-index: " + (max + 20) + ";", "}", ".annotator-filter {", "  z-index: " + (max + 10) + ";", "}"].join("\n"));
      return this;
    };

    Annotator.prototype.getHref = function() {
      var uri;
      uri = decodeURIComponent(document.location.href);
      if (document.location.hash) uri = uri.slice(0, -1 * location.hash.length);
      $('meta[property^="og:url"]').each(function() {
        return uri = decodeURIComponent(this.content);
      });
      $('link[rel^="canonical"]').each(function() {
        return uri = decodeURIComponent(this.href);
      });
      return uri;
    };

    Annotator.prototype.getRangeSelector = function(range) {
      var selector, sr;
      sr = range.serialize(this.wrapper[0]);
      return selector = {
        type: "RangeSelector",
        startContainer: sr.startContainer,
        startOffset: sr.startOffset,
        endContainer: sr.endContainer,
        endOffset: sr.endOffset
      };
    };

    Annotator.prototype.getTextQuoteSelector = function(range) {
      var endOffset, prefix, quote, rangeEnd, rangeStart, selector, startOffset, suffix, _ref2;
      if (range == null) {
        throw new Error("Called getTextQuoteSelector(range) with null range!");
      }
      rangeStart = range.start;
      if (rangeStart == null) {
        throw new Error("Called getTextQuoteSelector(range) on a range with no valid start.");
      }
      startOffset = (this.domMapper.getInfoForNode(rangeStart)).start;
      rangeEnd = range.end;
      if (rangeEnd == null) {
        throw new Error("Called getTextQuoteSelector(range) on a range with no valid end.");
      }
      endOffset = (this.domMapper.getInfoForNode(rangeEnd)).end;
      quote = this.domMapper.getContentForCharRange(startOffset, endOffset);
      _ref2 = this.domMapper.getContextForCharRange(startOffset, endOffset), prefix = _ref2[0], suffix = _ref2[1];
      return selector = {
        type: "TextQuoteSelector",
        exact: quote,
        prefix: prefix,
        suffix: suffix
      };
    };

    Annotator.prototype.getTextPositionSelector = function(range) {
      var endOffset, selector, startOffset;
      startOffset = (this.domMapper.getInfoForNode(range.start)).start;
      endOffset = (this.domMapper.getInfoForNode(range.end)).end;
      return selector = {
        type: "TextPositionSelector",
        start: startOffset,
        end: endOffset
      };
    };

    Annotator.prototype.getQuoteForTarget = function(target) {
      var selector;
      selector = this.findSelector(target.selector, "TextQuoteSelector");
      if (selector != null) {
        return this.normalizeString(selector.exact);
      } else {
        return null;
      }
    };

    Annotator.prototype.getSelectedTargets = function() {
      var browserRange, i, normedRange, r, rangesToIgnore, realRange, selection, source, targets, _k, _len3,
        _this = this;
      if (this.domMapper == null) {
        throw new Error("Can not execute getSelectedTargets() before _setupMatching()!");
      }
      if (!this.wrapper) {
        throw new Error("Can not execute getSelectedTargets() before @wrapper is configured!");
      }
      selection = util.getGlobal().getSelection();
      source = this.getHref();
      targets = [];
      rangesToIgnore = [];
      if (!selection.isCollapsed) {
        targets = (function() {
          var _ref2, _results;
          _results = [];
          for (i = 0, _ref2 = selection.rangeCount; 0 <= _ref2 ? i < _ref2 : i > _ref2; 0 <= _ref2 ? i++ : i--) {
            realRange = selection.getRangeAt(i);
            browserRange = new Range.BrowserRange(realRange);
            normedRange = browserRange.normalize().limit(this.wrapper[0]);
            if (normedRange === null) rangesToIgnore.push(r);
            _results.push({
              selector: [this.getRangeSelector(normedRange), this.getTextQuoteSelector(normedRange), this.getTextPositionSelector(normedRange)],
              source: source
            });
          }
          return _results;
        }).call(this);
        selection.removeAllRanges();
      }
      for (_k = 0, _len3 = rangesToIgnore.length; _k < _len3; _k++) {
        r = rangesToIgnore[_k];
        selection.addRange(r);
      }
      return $.grep(targets, function(target) {
        var range, selector;
        selector = _this.findSelector(target.selector, "RangeSelector");
        if (selector != null) {
          range = (Range.sniff(selector)).normalize(_this.wrapper[0]);
          if (range != null) {
            selection.addRange(range.toRange());
            return true;
          }
        }
      });
    };

    Annotator.prototype.createAnnotation = function() {
      var annotation;
      annotation = {};
      this.publish('beforeAnnotationCreated', [annotation]);
      return annotation;
    };

    Annotator.prototype.normalizeString = function(string) {
      return string.replace(/\s{2,}/g, " ");
    };

    Annotator.prototype.findSelector = function(selectors, type) {
      var selector, _k, _len3;
      for (_k = 0, _len3 = selectors.length; _k < _len3; _k++) {
        selector = selectors[_k];
        if (selector.type === type) return selector;
      }
      return null;
    };

    Annotator.prototype.findAnchorFromRangeSelector = function(target) {
      var content, currentQuote, endInfo, endOffset, normalizedRange, savedQuote, selector, startInfo, startOffset;
      selector = this.findSelector(target.selector, "RangeSelector");
      if (selector == null) return null;
      try {
        normalizedRange = Range.sniff(selector).normalize(this.wrapper[0]);
        savedQuote = this.getQuoteForTarget(target);
        if (savedQuote != null) {
          startInfo = this.domMapper.getInfoForNode(normalizedRange.start);
          startOffset = startInfo.start;
          endInfo = this.domMapper.getInfoForNode(normalizedRange.end);
          endOffset = endInfo.end;
          content = this.domMapper.getContentForCharRange(startOffset, endOffset);
          currentQuote = this.normalizeString(content);
          if (currentQuote !== savedQuote) {
            console.log("Could not apply XPath selector to current document             because the quote has changed. (Saved quote is '" + savedQuote + "'.             Current quote is '" + currentQuote + "'.)");
            return null;
          } else {
            console.log("Saved quote matches.");
          }
        } else {
          console.log("No saved quote, nothing to compare. Assume that it's OK.");
        }
        return {
          range: normalizedRange,
          quote: savedQuote
        };
      } catch (exception) {
        if (exception instanceof Range.RangeError) {
          console.log("Could not apply XPath selector to current document. \          The document structure may have changed.");
          return null;
        } else {
          throw exception;
        }
      }
    };

    Annotator.prototype.findAnchorFromPositionSelector = function(target) {
      var browserRange, content, currentQuote, mappings, normalizedRange, savedQuote, selector;
      selector = this.findSelector(target.selector, "TextPositionSelector");
      if (selector == null) return null;
      savedQuote = this.getQuoteForTarget(target);
      if (savedQuote != null) {
        content = this.domMapper.getContentForCharRange(selector.start, selector.end);
        currentQuote = this.normalizeString(content);
        if (currentQuote !== savedQuote) {
          console.log("Could not apply position selector to current document           because the quote has changed. (Saved quote is '" + savedQuote + "'.           Current quote is '" + currentQuote + "'.)");
          return null;
        } else {
          console.log("Saved quote matches.");
        }
      } else {
        console.log("No saved quote, nothing to compare. Assume that it's okay.");
      }
      mappings = this.domMapper.getMappingsForCharRange(selector.start, selector.end);
      browserRange = new Range.BrowserRange(mappings.realRange);
      normalizedRange = browserRange.normalize(this.wrapper[0]);
      return {
        range: normalizedRange,
        quote: savedQuote
      };
    };

    Annotator.prototype.findAnchorWithTwoPhaseFuzzyMatching = function(target) {
      var anchor, browserRange, expectedEnd, expectedStart, match, normalizedRange, options, posSelector, prefix, quote, quoteSelector, result, suffix;
      quoteSelector = this.findSelector(target.selector, "TextQuoteSelector");
      prefix = quoteSelector != null ? quoteSelector.prefix : void 0;
      suffix = quoteSelector != null ? quoteSelector.suffix : void 0;
      quote = quoteSelector != null ? quoteSelector.exact : void 0;
      if (!((prefix != null) && (suffix != null))) return null;
      posSelector = this.findSelector(target.selector, "TextPositionSelector");
      expectedStart = posSelector != null ? posSelector.start : void 0;
      expectedEnd = posSelector != null ? posSelector.end : void 0;
      options = {
        contextMatchDistance: this.domMapper.getDocLength() * 2,
        contextMatchThreshold: 0.5,
        patternMatchThreshold: 0.5
      };
      result = this.domMatcher.searchFuzzyWithContext(prefix, suffix, quote, expectedStart, expectedEnd, false, null, options);
      if (!result.matches.length) {
        console.log("Fuzzy matching did not return any results. Giving up on two-phase strategy.");
        return null;
      }
      match = result.matches[0];
      console.log("Fuzzy found match:");
      console.log(match);
      browserRange = new Range.BrowserRange(match.realRange);
      normalizedRange = browserRange.normalize(this.wrapper[0]);
      anchor = {
        range: normalizedRange,
        quote: !match.exact ? match.found : void 0,
        diffHTML: !match.exact ? match.comparison.diffHTML : void 0
      };
      return anchor;
    };

    Annotator.prototype.findAnchorWithFuzzyMatching = function(target) {
      var anchor, browserRange, expectedStart, len, match, normalizedRange, options, posSelector, quote, quoteSelector, result;
      quoteSelector = this.findSelector(target.selector, "TextQuoteSelector");
      quote = quoteSelector != null ? quoteSelector.exact : void 0;
      if (quote == null) return null;
      posSelector = this.findSelector(target.selector, "TextPositionSelector");
      expectedStart = posSelector != null ? posSelector.start : void 0;
      len = this.domMapper.getDocLength();
      if (expectedStart == null) expectedStart = len / 2;
      options = {
        matchDistance: len,
        withFuzzyComparison: true
      };
      result = this.domMatcher.searchFuzzy(quote, expectedStart, false, null, options);
      if (!result.matches.length) {
        console.log("Fuzzy matching did not return any results. Giving up on one-phase strategy.");
        return null;
      }
      match = result.matches[0];
      console.log("Fuzzy found match:");
      console.log(match);
      browserRange = new Range.BrowserRange(match.realRange);
      normalizedRange = browserRange.normalize(this.wrapper[0]);
      anchor = {
        range: normalizedRange,
        quote: !match.exact ? match.found : void 0,
        diffHTML: !match.exact ? match.comparison.diffHTML : void 0
      };
      return anchor;
    };

    Annotator.prototype.findAnchor = function(target) {
      var anchor;
      if (target == null) {
        throw new Error("Trying to find anchor for null target!");
      }
      console.log("Trying to find anchor for target: ");
      console.log(target);
      anchor = this.findAnchorFromRangeSelector(target);
      if (anchor == null) anchor = this.findAnchorFromPositionSelector(target);
      if (anchor == null) {
        anchor = this.findAnchorWithTwoPhaseFuzzyMatching(target);
      }
      if (anchor == null) anchor = this.findAnchorWithFuzzyMatching(target);
      return anchor;
    };

    Annotator.prototype.setupAnnotation = function(annotation) {
      var anchor, normed, normedRanges, root, t, _k, _l, _len3, _len4, _ref2;
      root = this.wrapper[0];
      annotation.target || (annotation.target = this.selectedTargets);
      if (annotation.target == null) {
        throw new Error("Can not run setupAnnotation(), since @selectedTargets is null!");
      }
      if (!(annotation.target instanceof Array)) {
        annotation.target = [annotation.target];
      }
      normedRanges = [];
      annotation.quote = [];
      _ref2 = annotation.target;
      for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
        t = _ref2[_k];
        try {
          anchor = this.findAnchor(t);
          t.quote = anchor.quote;
          t.diffHTML = anchor.diffHTML;
          if ((anchor != null ? anchor.range : void 0) != null) {
            normedRanges.push(anchor.range);
            annotation.quote.push(t.quote);
          } else {
            console.log("Could not find anchor for annotation target '" + t.id + "' (for annotation '" + annotation.id + "').");
          }
        } catch (exception) {
          if (exception.stack != null) console.log(exception.stack);
          console.log(exception.message);
          console.log(exception);
        }
      }
      annotation.ranges = [];
      annotation.highlights = [];
      for (_l = 0, _len4 = normedRanges.length; _l < _len4; _l++) {
        normed = normedRanges[_l];
        annotation.ranges.push(normed.serialize(this.wrapper[0], '.annotator-hl'));
        $.merge(annotation.highlights, this.highlightRange(normed));
      }
      annotation.quote = annotation.quote.join(' / ');
      $(annotation.highlights).data('annotation', annotation);
      return annotation;
    };

    Annotator.prototype.updateAnnotation = function(annotation) {
      this.publish('beforeAnnotationUpdated', [annotation]);
      this.publish('annotationUpdated', [annotation]);
      return annotation;
    };

    Annotator.prototype.deleteAnnotation = function(annotation) {
      var child, h, _k, _len3, _ref2;
      if (annotation.highlights != null) {
        _ref2 = annotation.highlights;
        for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
          h = _ref2[_k];
          if (!(h.parentNode != null)) continue;
          child = h.childNodes[0];
          $(h).replaceWith(h.childNodes);
          window.DomTextMapper.changed(child.parentNode, "removed hilite (annotation deleted)");
        }
      }
      this.publish('annotationDeleted', [annotation]);
      return annotation;
    };

    Annotator.prototype.loadAnnotations = function(annotations) {
      var clone, loader,
        _this = this;
      if (annotations == null) annotations = [];
      loader = function(annList) {
        var n, now, _k, _len3;
        if (annList == null) annList = [];
        now = annList.splice(0, 10);
        for (_k = 0, _len3 = now.length; _k < _len3; _k++) {
          n = now[_k];
          _this.setupAnnotation(n);
        }
        if (annList.length > 0) {
          return setTimeout((function() {
            return loader(annList);
          }), 10);
        } else {
          return _this.publish('annotationsLoaded', [clone]);
        }
      };
      clone = annotations.slice();
      if (annotations.length) loader(annotations);
      return this;
    };

    Annotator.prototype.dumpAnnotations = function() {
      if (this.plugins['Store']) {
        return this.plugins['Store'].dumpAnnotations();
      } else {
        return console.warn(_t("Can't dump annotations without Store plugin."));
      }
    };

    Annotator.prototype.highlightRange = function(normedRange, cssClass) {
      var hl, node, r, white, _k, _len3, _ref2, _results;
      if (cssClass == null) cssClass = 'annotator-hl';
      white = /^\s*$/;
      hl = $("<span class='" + cssClass + "'></span>");
      _ref2 = normedRange.textNodes();
      _results = [];
      for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
        node = _ref2[_k];
        if (!(!white.test(node.nodeValue))) continue;
        r = $(node).wrapAll(hl).parent().show()[0];
        window.DomTextMapper.changed(node, "created hilite");
        _results.push(r);
      }
      return _results;
    };

    Annotator.prototype.highlightRanges = function(normedRanges, cssClass) {
      var highlights, r, _k, _len3;
      if (cssClass == null) cssClass = 'annotator-hl';
      highlights = [];
      for (_k = 0, _len3 = normedRanges.length; _k < _len3; _k++) {
        r = normedRanges[_k];
        $.merge(highlights, this.highlightRange(r, cssClass));
      }
      return highlights;
    };

    Annotator.prototype.addPlugin = function(name, options) {
      var klass, _base;
      if (this.plugins[name]) {
        console.error(_t("You cannot have more than one instance of any plugin."));
      } else {
        klass = Annotator.Plugin[name];
        if (typeof klass === 'function') {
          this.plugins[name] = new klass(this.element[0], options);
          this.plugins[name].annotator = this;
          if (typeof (_base = this.plugins[name]).pluginInit === "function") {
            _base.pluginInit();
          }
        } else {
          console.error(_t("Could not load ") + name + _t(" plugin. Have you included the appropriate <script> tag?"));
        }
      }
      return this;
    };

    Annotator.prototype.showEditor = function(annotation, location) {
      this.editor.element.css(location);
      this.editor.load(annotation);
      this.publish('annotationEditorShown', [this.editor, annotation]);
      return this;
    };

    Annotator.prototype.onEditorHide = function() {
      this.publish('annotationEditorHidden', [this.editor]);
      return this.ignoreMouseup = false;
    };

    Annotator.prototype.onEditorSubmit = function(annotation) {
      return this.publish('annotationEditorSubmit', [this.editor, annotation]);
    };

    Annotator.prototype.showViewer = function(annotations, location) {
      this.viewer.element.css(location);
      this.viewer.load(annotations);
      return this.publish('annotationViewerShown', [this.viewer, annotations]);
    };

    Annotator.prototype.startViewerHideTimer = function() {
      if (!this.viewerHideTimer) {
        return this.viewerHideTimer = setTimeout(this.viewer.hide, 250);
      }
    };

    Annotator.prototype.clearViewerHideTimer = function() {
      clearTimeout(this.viewerHideTimer);
      return this.viewerHideTimer = false;
    };

    Annotator.prototype.checkForStartSelection = function(event) {
      if (!(event && this.isAnnotator(event.target))) {
        this.startViewerHideTimer();
        return this.mouseIsDown = true;
      }
    };

    Annotator.prototype.checkForEndSelection = function(event) {
      var container, range, selector, target, _k, _len3, _ref2;
      this.mouseIsDown = false;
      if (this.ignoreMouseup) return;
      this.selectedTargets = this.getSelectedTargets();
      _ref2 = this.selectedTargets;
      for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
        target = _ref2[_k];
        selector = this.findSelector(target.selector, "RangeSelector");
        range = (Range.sniff(selector)).normalize(this.wrapper[0]);
        container = range.commonAncestor;
        if ($(container).hasClass('annotator-hl')) {
          container = $(container).parents('[class^=annotator-hl]')[0];
        }
        if (this.isAnnotator(container)) return;
      }
      if (event && this.selectedTargets.length) {
        return this.adder.css(util.mousePosition(event, this.wrapper[0])).show();
      } else {
        return this.adder.hide();
      }
    };

    Annotator.prototype.isAnnotator = function(element) {
      return !!$(element).parents().andSelf().filter('[class^=annotator-]').not(this.wrapper).length;
    };

    Annotator.prototype.onHighlightMouseover = function(event) {
      var annotations;
      this.clearViewerHideTimer();
      if (this.mouseIsDown || this.viewer.isShown()) return false;
      annotations = $(event.target).parents('.annotator-hl').andSelf().map(function() {
        return $(this).data("annotation");
      });
      return this.showViewer($.makeArray(annotations), util.mousePosition(event, this.wrapper[0]));
    };

    Annotator.prototype.onAdderMousedown = function(event) {
      if (event != null) event.preventDefault();
      return this.ignoreMouseup = true;
    };

    Annotator.prototype.onAdderClick = function(event) {
      var annotation, cancel, cleanup, position, save,
        _this = this;
      if (event != null) event.preventDefault();
      position = this.adder.position();
      this.adder.hide();
      annotation = this.createAnnotation();
      annotation = this.setupAnnotation(annotation);
      $(annotation.highlights).addClass('annotator-hl-temporary');
      save = function() {
        cleanup();
        $(annotation.highlights).removeClass('annotator-hl-temporary');
        return _this.publish('annotationCreated', [annotation]);
      };
      cancel = function() {
        cleanup();
        return _this.deleteAnnotation(annotation);
      };
      cleanup = function() {
        _this.unsubscribe('annotationEditorHidden', cancel);
        return _this.unsubscribe('annotationEditorSubmit', save);
      };
      this.subscribe('annotationEditorHidden', cancel);
      this.subscribe('annotationEditorSubmit', save);
      return this.showEditor(annotation, position);
    };

    Annotator.prototype.onEditAnnotation = function(annotation) {
      var cleanup, offset, update,
        _this = this;
      offset = this.viewer.element.position();
      update = function() {
        cleanup();
        return _this.updateAnnotation(annotation);
      };
      cleanup = function() {
        _this.unsubscribe('annotationEditorHidden', cleanup);
        return _this.unsubscribe('annotationEditorSubmit', update);
      };
      this.subscribe('annotationEditorHidden', cleanup);
      this.subscribe('annotationEditorSubmit', update);
      this.viewer.hide();
      return this.showEditor(annotation, offset);
    };

    Annotator.prototype.onDeleteAnnotation = function(annotation) {
      this.viewer.hide();
      return this.deleteAnnotation(annotation);
    };

    return Annotator;

  })(Delegator);

  Annotator.Plugin = (function(_super) {

    __extends(Plugin, _super);

    function Plugin(element, options) {
      Plugin.__super__.constructor.apply(this, arguments);
    }

    Plugin.prototype.pluginInit = function() {};

    return Plugin;

  })(Delegator);

  g = util.getGlobal();

  if (!(((_ref2 = g.document) != null ? _ref2.evaluate : void 0) != null)) {
    $.getScript('http://assets.annotateit.org/vendor/xpath.min.js');
  }

  if (!(g.getSelection != null)) {
    $.getScript('http://assets.annotateit.org/vendor/ierange.min.js');
  }

  if (!(g.JSON != null)) {
    $.getScript('http://assets.annotateit.org/vendor/json2.min.js');
  }

  Annotator.$ = $;

  Annotator.Delegator = Delegator;

  Annotator.Range = Range;

  Annotator._t = _t;

  Annotator.supported = function() {
    return (function() {
      return !!this.getSelection;
    })();
  };

  Annotator.noConflict = function() {
    util.getGlobal().Annotator = _Annotator;
    return this;
  };

  $.plugin('annotator', Annotator);

  this.Annotator = Annotator;

  Annotator.Widget = (function(_super) {

    __extends(Widget, _super);

    Widget.prototype.classes = {
      hide: 'annotator-hide',
      invert: {
        x: 'annotator-invert-x',
        y: 'annotator-invert-y'
      }
    };

    function Widget(element, options) {
      Widget.__super__.constructor.apply(this, arguments);
      this.classes = $.extend({}, Annotator.Widget.prototype.classes, this.classes);
    }

    Widget.prototype.checkOrientation = function() {
      var current, offset, viewport, widget, window;
      this.resetOrientation();
      window = $(util.getGlobal());
      widget = this.element.children(":first");
      offset = widget.offset();
      viewport = {
        top: window.scrollTop(),
        right: window.width() + window.scrollLeft()
      };
      current = {
        top: offset.top,
        right: offset.left + widget.width()
      };
      if ((current.top - viewport.top) < 0) this.invertY();
      if ((current.right - viewport.right) > 0) this.invertX();
      return this;
    };

    Widget.prototype.resetOrientation = function() {
      this.element.removeClass(this.classes.invert.x).removeClass(this.classes.invert.y);
      return this;
    };

    Widget.prototype.invertX = function() {
      this.element.addClass(this.classes.invert.x);
      return this;
    };

    Widget.prototype.invertY = function() {
      this.element.addClass(this.classes.invert.y);
      return this;
    };

    Widget.prototype.isInvertedY = function() {
      return this.element.hasClass(this.classes.invert.y);
    };

    Widget.prototype.isInvertedX = function() {
      return this.element.hasClass(this.classes.invert.x);
    };

    return Widget;

  })(Delegator);

  Annotator.Editor = (function(_super) {

    __extends(Editor, _super);

    Editor.prototype.events = {
      "form submit": "submit",
      ".annotator-save click": "submit",
      ".annotator-cancel click": "hide",
      ".annotator-cancel mouseover": "onCancelButtonMouseover",
      "textarea keydown": "processKeypress"
    };

    Editor.prototype.classes = {
      hide: 'annotator-hide',
      focus: 'annotator-focus'
    };

    Editor.prototype.html = "<div class=\"annotator-outer annotator-editor\">\n  <form class=\"annotator-widget\">\n    <ul class=\"annotator-listing\"></ul>\n    <div class=\"annotator-controls\">\n      <a href=\"#cancel\" class=\"annotator-cancel\">" + _t('Cancel') + "</a>\n<a href=\"#save\" class=\"annotator-save annotator-focus\">" + _t('Save') + "</a>\n    </div>\n  </form>\n</div>";

    Editor.prototype.options = {};

    function Editor(options) {
      this.onCancelButtonMouseover = __bind(this.onCancelButtonMouseover, this);
      this.processKeypress = __bind(this.processKeypress, this);
      this.submit = __bind(this.submit, this);
      this.load = __bind(this.load, this);
      this.hide = __bind(this.hide, this);
      this.show = __bind(this.show, this);      Editor.__super__.constructor.call(this, $(this.html)[0], options);
      this.fields = [];
      this.annotation = {};
    }

    Editor.prototype.show = function(event) {
      util.preventEventDefault(event);
      this.element.removeClass(this.classes.hide);
      this.element.find('.annotator-save').addClass(this.classes.focus);
      this.checkOrientation();
      this.element.find(":input:first").focus();
      this.setupDraggables();
      return this.publish('show');
    };

    Editor.prototype.hide = function(event) {
      util.preventEventDefault(event);
      this.element.addClass(this.classes.hide);
      return this.publish('hide');
    };

    Editor.prototype.load = function(annotation) {
      var field, _k, _len3, _ref3;
      this.annotation = annotation;
      this.publish('load', [this.annotation]);
      _ref3 = this.fields;
      for (_k = 0, _len3 = _ref3.length; _k < _len3; _k++) {
        field = _ref3[_k];
        field.load(field.element, this.annotation);
      }
      return this.show();
    };

    Editor.prototype.submit = function(event) {
      var field, _k, _len3, _ref3;
      util.preventEventDefault(event);
      _ref3 = this.fields;
      for (_k = 0, _len3 = _ref3.length; _k < _len3; _k++) {
        field = _ref3[_k];
        field.submit(field.element, this.annotation);
      }
      this.publish('save', [this.annotation]);
      return this.hide();
    };

    Editor.prototype.addField = function(options) {
      var element, field, input;
      field = $.extend({
        id: 'annotator-field-' + util.uuid(),
        type: 'input',
        label: '',
        load: function() {},
        submit: function() {}
      }, options);
      input = null;
      element = $('<li class="annotator-item" />');
      field.element = element[0];
      switch (field.type) {
        case 'textarea':
          input = $('<textarea />');
          break;
        case 'input':
        case 'checkbox':
          input = $('<input />');
      }
      element.append(input);
      input.attr({
        id: field.id,
        placeholder: field.label
      });
      if (field.type === 'checkbox') {
        input[0].type = 'checkbox';
        element.addClass('annotator-checkbox');
        element.append($('<label />', {
          "for": field.id,
          html: field.label
        }));
      }
      this.element.find('ul:first').append(element);
      this.fields.push(field);
      return field.element;
    };

    Editor.prototype.checkOrientation = function() {
      var controls, list;
      Editor.__super__.checkOrientation.apply(this, arguments);
      list = this.element.find('ul');
      controls = this.element.find('.annotator-controls');
      if (this.element.hasClass(this.classes.invert.y)) {
        controls.insertBefore(list);
      } else if (controls.is(':first-child')) {
        controls.insertAfter(list);
      }
      return this;
    };

    Editor.prototype.processKeypress = function(event) {
      if (event.keyCode === 27) {
        return this.hide();
      } else if (event.keyCode === 13 && !event.shiftKey) {
        return this.submit();
      }
    };

    Editor.prototype.onCancelButtonMouseover = function() {
      return this.element.find('.' + this.classes.focus).removeClass(this.classes.focus);
    };

    Editor.prototype.setupDraggables = function() {
      var classes, controls, cornerItem, editor, mousedown, onMousedown, onMousemove, onMouseup, resize, textarea, throttle,
        _this = this;
      this.element.find('.annotator-resize').remove();
      if (this.element.hasClass(this.classes.invert.y)) {
        cornerItem = this.element.find('.annotator-item:last');
      } else {
        cornerItem = this.element.find('.annotator-item:first');
      }
      if (cornerItem) {
        $('<span class="annotator-resize"></span>').appendTo(cornerItem);
      }
      mousedown = null;
      classes = this.classes;
      editor = this.element;
      textarea = null;
      resize = editor.find('.annotator-resize');
      controls = editor.find('.annotator-controls');
      throttle = false;
      onMousedown = function(event) {
        if (event.target === this) {
          mousedown = {
            element: this,
            top: event.pageY,
            left: event.pageX
          };
          textarea = editor.find('textarea:first');
          $(window).bind({
            'mouseup.annotator-editor-resize': onMouseup,
            'mousemove.annotator-editor-resize': onMousemove
          });
          return event.preventDefault();
        }
      };
      onMouseup = function() {
        mousedown = null;
        return $(window).unbind('.annotator-editor-resize');
      };
      onMousemove = function(event) {
        var diff, directionX, directionY, height, width;
        if (mousedown && throttle === false) {
          diff = {
            top: event.pageY - mousedown.top,
            left: event.pageX - mousedown.left
          };
          if (mousedown.element === resize[0]) {
            height = textarea.outerHeight();
            width = textarea.outerWidth();
            directionX = editor.hasClass(classes.invert.x) ? -1 : 1;
            directionY = editor.hasClass(classes.invert.y) ? 1 : -1;
            textarea.height(height + (diff.top * directionY));
            textarea.width(width + (diff.left * directionX));
            if (textarea.outerHeight() !== height) mousedown.top = event.pageY;
            if (textarea.outerWidth() !== width) mousedown.left = event.pageX;
          } else if (mousedown.element === controls[0]) {
            editor.css({
              top: parseInt(editor.css('top'), 10) + diff.top,
              left: parseInt(editor.css('left'), 10) + diff.left
            });
            mousedown.top = event.pageY;
            mousedown.left = event.pageX;
          }
          throttle = true;
          return setTimeout(function() {
            return throttle = false;
          }, 1000 / 60);
        }
      };
      resize.bind('mousedown', onMousedown);
      return controls.bind('mousedown', onMousedown);
    };

    return Editor;

  })(Annotator.Widget);

  Annotator.Viewer = (function(_super) {

    __extends(Viewer, _super);

    Viewer.prototype.events = {
      ".annotator-edit click": "onEditClick",
      ".annotator-delete click": "onDeleteClick"
    };

    Viewer.prototype.classes = {
      hide: 'annotator-hide',
      showControls: 'annotator-visible'
    };

    Viewer.prototype.html = {
      element: "<div class=\"annotator-outer annotator-viewer\">\n  <ul class=\"annotator-widget annotator-listing\"></ul>\n</div>",
      item: "<li class=\"annotator-annotation annotator-item\">\n  <span class=\"annotator-controls\">\n    <a href=\"#\" title=\"View as webpage\" class=\"annotator-link\">View as webpage</a>\n    <button title=\"Edit\" class=\"annotator-edit\">Edit</button>\n    <button title=\"Delete\" class=\"annotator-delete\">Delete</button>\n  </span>\n</li>"
    };

    Viewer.prototype.options = {
      readOnly: false
    };

    function Viewer(options) {
      this.onDeleteClick = __bind(this.onDeleteClick, this);
      this.onEditClick = __bind(this.onEditClick, this);
      this.load = __bind(this.load, this);
      this.hide = __bind(this.hide, this);
      this.show = __bind(this.show, this);      Viewer.__super__.constructor.call(this, $(this.html.element)[0], options);
      this.item = $(this.html.item)[0];
      this.fields = [];
      this.annotations = [];
    }

    Viewer.prototype.show = function(event) {
      var controls,
        _this = this;
      util.preventEventDefault(event);
      controls = this.element.find('.annotator-controls').addClass(this.classes.showControls);
      setTimeout((function() {
        return controls.removeClass(_this.classes.showControls);
      }), 500);
      this.element.removeClass(this.classes.hide);
      return this.checkOrientation().publish('show');
    };

    Viewer.prototype.isShown = function() {
      return !this.element.hasClass(this.classes.hide);
    };

    Viewer.prototype.hide = function(event) {
      util.preventEventDefault(event);
      this.element.addClass(this.classes.hide);
      return this.publish('hide');
    };

    Viewer.prototype.load = function(annotations) {
      var annotation, controller, controls, del, edit, element, field, item, link, links, list, _k, _l, _len3, _len4, _ref3, _ref4;
      this.annotations = annotations || [];
      list = this.element.find('ul:first').empty();
      _ref3 = this.annotations;
      for (_k = 0, _len3 = _ref3.length; _k < _len3; _k++) {
        annotation = _ref3[_k];
        item = $(this.item).clone().appendTo(list).data('annotation', annotation);
        controls = item.find('.annotator-controls');
        link = controls.find('.annotator-link');
        edit = controls.find('.annotator-edit');
        del = controls.find('.annotator-delete');
        links = new LinkParser(annotation.links || []).get('alternate', {
          'type': 'text/html'
        });
        if (links.length === 0 || !(links[0].href != null)) {
          link.remove();
        } else {
          link.attr('href', links[0].href);
        }
        if (this.options.readOnly) {
          edit.remove();
          del.remove();
        } else {
          controller = {
            showEdit: function() {
              return edit.removeAttr('disabled');
            },
            hideEdit: function() {
              return edit.attr('disabled', 'disabled');
            },
            showDelete: function() {
              return del.removeAttr('disabled');
            },
            hideDelete: function() {
              return del.attr('disabled', 'disabled');
            }
          };
        }
        _ref4 = this.fields;
        for (_l = 0, _len4 = _ref4.length; _l < _len4; _l++) {
          field = _ref4[_l];
          element = $(field.element).clone().appendTo(item)[0];
          field.load(element, annotation, controller);
        }
      }
      this.publish('load', [this.annotations]);
      return this.show();
    };

    Viewer.prototype.addField = function(options) {
      var field;
      field = $.extend({
        load: function() {}
      }, options);
      field.element = $('<div />')[0];
      this.fields.push(field);
      field.element;
      return this;
    };

    Viewer.prototype.onEditClick = function(event) {
      return this.onButtonClick(event, 'edit');
    };

    Viewer.prototype.onDeleteClick = function(event) {
      return this.onButtonClick(event, 'delete');
    };

    Viewer.prototype.onButtonClick = function(event, type) {
      var item;
      item = $(event.target).parents('.annotator-annotation');
      return this.publish(type, [item.data('annotation')]);
    };

    return Viewer;

  })(Annotator.Widget);

  LinkParser = (function() {

    function LinkParser(data) {
      this.data = data;
    }

    LinkParser.prototype.get = function(rel, cond) {
      var d, k, keys, match, v, _k, _len3, _ref3, _results;
      if (cond == null) cond = {};
      cond = $.extend({}, cond, {
        rel: rel
      });
      keys = (function() {
        var _results;
        _results = [];
        for (k in cond) {
          if (!__hasProp.call(cond, k)) continue;
          v = cond[k];
          _results.push(k);
        }
        return _results;
      })();
      _ref3 = this.data;
      _results = [];
      for (_k = 0, _len3 = _ref3.length; _k < _len3; _k++) {
        d = _ref3[_k];
        match = keys.reduce((function(m, k) {
          return m && (d[k] === cond[k]);
        }), true);
        if (match) {
          _results.push(d);
        } else {
          continue;
        }
      }
      return _results;
    };

    return LinkParser;

  })();

  Annotator = Annotator || {};

  Annotator.Notification = (function(_super) {

    __extends(Notification, _super);

    Notification.prototype.events = {
      "click": "hide"
    };

    Notification.prototype.options = {
      html: "<div class='annotator-notice'></div>",
      classes: {
        show: "annotator-notice-show",
        info: "annotator-notice-info",
        success: "annotator-notice-success",
        error: "annotator-notice-error"
      }
    };

    function Notification(options) {
      this.hide = __bind(this.hide, this);
      this.show = __bind(this.show, this);      Notification.__super__.constructor.call(this, $(this.options.html).appendTo(document.body)[0], options);
    }

    Notification.prototype.show = function(message, status) {
      if (status == null) status = Annotator.Notification.INFO;
      $(this.element).addClass(this.options.classes.show).addClass(this.options.classes[status]).escape(message || "");
      setTimeout(this.hide, 5000);
      return this;
    };

    Notification.prototype.hide = function() {
      $(this.element).removeClass(this.options.classes.show);
      return this;
    };

    return Notification;

  })(Delegator);

  Annotator.Notification.INFO = 'show';

  Annotator.Notification.SUCCESS = 'success';

  Annotator.Notification.ERROR = 'error';

  $(function() {
    var notification;
    notification = new Annotator.Notification;
    Annotator.showNotification = notification.show;
    return Annotator.hideNotification = notification.hide;
  });

}).call(this);
