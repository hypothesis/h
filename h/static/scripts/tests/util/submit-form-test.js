'use strict';

var submitForm = require('../../util/submit-form');

var lastRequest;
function FakeXMLHttpRequest() {
  lastRequest = this; // eslint-disable-line consistent-this
  this.open = sinon.stub();
  this.setRequestHeader = sinon.stub();
  this.send = sinon.stub();

  var self = this;
  setTimeout(function () {
    self.readyState = XMLHttpRequest.DONE;
    if (!self.status) {
      self.status = 200;
    }
    self.responseText = 'response';
    self.onreadystatechange();
  }, 0);
}
FakeXMLHttpRequest.DONE = 4;

describe('submitForm', function () {
  function createForm() {
    var form = document.createElement('form');
    form.action = 'http://example.org/things';
    form.method = 'POST';
    form.innerHTML = '<input name="field" value="value">';
    return form;
  }

  it('submits the form data', function () {
    var form = createForm();
    return submitForm(form, FakeXMLHttpRequest).then(function () {
      var arg = lastRequest.send.getCall(0).args[0];
      assert.instanceOf(arg, FormData);
    });
  });

  it('returns a rejected promise if the XHR request fails', function () {
    var form = createForm();
    var done = submitForm(form, FakeXMLHttpRequest);
    lastRequest.status = 400;
    return done.catch(function (err) {
      assert.deepEqual(err, {status: 400, form: 'response'});
    });
  });
});
