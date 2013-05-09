/*
** Annotator 1.2.6-dev-1545e1b
** https://github.com/okfn/annotator/
**
** Copyright 2012 Aron Carroll, Rufus Pollock, and Nick Stenning.
** Dual licensed under the MIT and GPLv3 licenses.
** https://github.com/okfn/annotator/blob/master/LICENSE
**
** Built at: 2013-05-05 23:19:10Z
*/

(function() {
  var base64Decode, base64UrlDecode, createDateFromISO8601, parseToken,
    __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

  createDateFromISO8601 = function(string) {
    var d, date, offset, regexp, time, _ref;
    regexp = "([0-9]{4})(-([0-9]{2})(-([0-9]{2})" + "(T([0-9]{2}):([0-9]{2})(:([0-9]{2})(\.([0-9]+))?)?" + "(Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?";
    d = string.match(new RegExp(regexp));
    offset = 0;
    date = new Date(d[1], 0, 1);
    if (d[3]) date.setMonth(d[3] - 1);
    if (d[5]) date.setDate(d[5]);
    if (d[7]) date.setHours(d[7]);
    if (d[8]) date.setMinutes(d[8]);
    if (d[10]) date.setSeconds(d[10]);
    if (d[12]) date.setMilliseconds(Number("0." + d[12]) * 1000);
    if (d[14]) {
      offset = (Number(d[16]) * 60) + Number(d[17]);
      offset *= (_ref = d[15] === '-') != null ? _ref : {
        1: -1
      };
    }
    offset -= date.getTimezoneOffset();
    time = Number(date) + (offset * 60 * 1000);
    date.setTime(Number(time));
    return date;
  };

  base64Decode = function(data) {
    var ac, b64, bits, dec, h1, h2, h3, h4, i, o1, o2, o3, tmp_arr;
    if (typeof atob !== "undefined" && atob !== null) {
      return atob(data);
    } else {
      b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
      i = 0;
      ac = 0;
      dec = "";
      tmp_arr = [];
      if (!data) return data;
      data += '';
      while (i < data.length) {
        h1 = b64.indexOf(data.charAt(i++));
        h2 = b64.indexOf(data.charAt(i++));
        h3 = b64.indexOf(data.charAt(i++));
        h4 = b64.indexOf(data.charAt(i++));
        bits = h1 << 18 | h2 << 12 | h3 << 6 | h4;
        o1 = bits >> 16 & 0xff;
        o2 = bits >> 8 & 0xff;
        o3 = bits & 0xff;
        if (h3 === 64) {
          tmp_arr[ac++] = String.fromCharCode(o1);
        } else if (h4 === 64) {
          tmp_arr[ac++] = String.fromCharCode(o1, o2);
        } else {
          tmp_arr[ac++] = String.fromCharCode(o1, o2, o3);
        }
      }
      return tmp_arr.join('');
    }
  };

  base64UrlDecode = function(data) {
    var i, m, _ref;
    m = data.length % 4;
    if (m !== 0) {
      for (i = 0, _ref = 4 - m; 0 <= _ref ? i < _ref : i > _ref; 0 <= _ref ? i++ : i--) {
        data += '=';
      }
    }
    data = data.replace(/-/g, '+');
    data = data.replace(/_/g, '/');
    return base64Decode(data);
  };

  parseToken = function(token) {
    var head, payload, sig, _ref;
    _ref = token.split('.'), head = _ref[0], payload = _ref[1], sig = _ref[2];
    return JSON.parse(base64UrlDecode(payload));
  };

  Annotator.Plugin.Auth = (function(_super) {

    __extends(Auth, _super);

    Auth.prototype.options = {
      token: null,
      tokenUrl: '/auth/token',
      autoFetch: true
    };

    function Auth(element, options) {
      Auth.__super__.constructor.apply(this, arguments);
      this.waitingForToken = [];
      if (this.options.token) {
        this.setToken(this.options.token);
      } else {
        this.requestToken();
      }
    }

    Auth.prototype.requestToken = function() {
      var _this = this;
      this.requestInProgress = true;
      return $.ajax({
        url: this.options.tokenUrl,
        dataType: 'text',
        xhrFields: {
          withCredentials: true
        }
      }).done(function(data, status, xhr) {
        return _this.setToken(data);
      }).fail(function(xhr, status, err) {
        var msg;
        msg = Annotator._t("Couldn't get auth token:");
        console.error("" + msg + " " + err, xhr);
        return Annotator.showNotification("" + msg + " " + xhr.responseText, Annotator.Notification.ERROR);
      }).always(function() {
        return _this.requestInProgress = false;
      });
    };

    Auth.prototype.setToken = function(token) {
      var _results,
        _this = this;
      this.token = token;
      this._unsafeToken = parseToken(token);
      if (this.haveValidToken()) {
        if (this.options.autoFetch) {
          this.refreshTimeout = setTimeout((function() {
            return _this.requestToken();
          }), (this.timeToExpiry() - 2) * 1000);
        }
        this.updateHeaders();
        _results = [];
        while (this.waitingForToken.length > 0) {
          _results.push(this.waitingForToken.pop()(this._unsafeToken));
        }
        return _results;
      } else {
        console.warn(Annotator._t("Didn't get a valid token."));
        if (this.options.autoFetch) {
          console.warn(Annotator._t("Getting a new token in 10s."));
          return setTimeout((function() {
            return _this.requestToken();
          }), 10 * 1000);
        }
      }
    };

    Auth.prototype.haveValidToken = function() {
      var allFields;
      allFields = this._unsafeToken && this._unsafeToken.issuedAt && this._unsafeToken.ttl && this._unsafeToken.consumerKey;
      return allFields && this.timeToExpiry() > 0;
    };

    Auth.prototype.timeToExpiry = function() {
      var expiry, issue, now, timeToExpiry;
      now = new Date().getTime() / 1000;
      issue = createDateFromISO8601(this._unsafeToken.issuedAt).getTime() / 1000;
      expiry = issue + this._unsafeToken.ttl;
      timeToExpiry = expiry - now;
      if (timeToExpiry > 0) {
        return timeToExpiry;
      } else {
        return 0;
      }
    };

    Auth.prototype.updateHeaders = function() {
      var current;
      current = this.element.data('annotator:headers');
      return this.element.data('annotator:headers', $.extend(current, {
        'x-annotator-auth-token': this.token
      }));
    };

    Auth.prototype.withToken = function(callback) {
      if (!(callback != null)) return;
      if (this.haveValidToken()) {
        return callback(this._unsafeToken);
      } else {
        this.waitingForToken.push(callback);
        if (!this.requestInProgress) return this.requestToken();
      }
    };

    return Auth;

  })(Annotator.Plugin);

}).call(this);
