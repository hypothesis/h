var main = require("../index");

exports["test index"] = function(assert) {
  assert.pass("Unit test running!");
};

exports["test index async"] = function(assert, done) {
  assert.pass("async Unit test running!");
  done();
};

require("sdk/test").run(exports);
