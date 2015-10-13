var TabErrorCache = require('../lib/tab-error-cache');

describe('TabErrorCache', function () {
 var cache;

 beforeEach(function () {
   cache = new TabErrorCache();
 });

 it('allows items to be set an retrieved', function () {
   var err = new Error('foo');
   cache.setTabError(1, err);
   assert.equal(cache.getTabError(1), err);
 });

 it('allows items to be removed', function () {
   var err = new Error('foo');
   cache.setTabError(1, err);
   cache.unsetTabError(1);
   assert.notEqual(cache.getTabError(1), err);
 });

 it('returns null if an item does not exist', function () {
   var err = new Error('foo');
   assert.isNull(cache.getTabError(1));
 });
});
