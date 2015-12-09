var draftsService = require('../drafts');

describe('drafts', function () {
  var drafts;

  beforeEach(function () {
    drafts = draftsService();
  });

  describe('.update', function () {
    it('should save changes', function () {
      var model = {id: 'foo'};
      assert.notOk(drafts.get(model));
      drafts.update(model, {isPrivate:true, tags:['foo'], text:'edit'});
      assert.deepEqual(
        drafts.get(model),
        {isPrivate: true, tags: ['foo'], text: 'edit'});
    });

    it('should replace existing drafts', function () {
      var model = {id: 'foo'};
      drafts.update(model, {isPrivate:true, tags:['foo'], text:'foo'});
      drafts.update(model, {isPrivate:true, tags:['foo'], text:'bar'});
      assert.equal(drafts.get(model).text, 'bar');
    });

    it('should replace existing drafts with the same ID', function () {
      var modelA = {id: 'foo'};
      var modelB = {id: 'foo'};
      drafts.update(modelA, {isPrivate:true, tags:['foo'], text:'foo'});
      drafts.update(modelB, {isPrivate:true, tags:['foo'], text:'bar'});
      assert.equal(drafts.get(modelA).text, 'bar');
    });
  });

  describe('.remove', function () {
    it('should remove drafts', function () {
      var model = {id: 'foo'};
      drafts.update(model, {text: 'bar'});
      drafts.remove(model);
      assert.notOk(drafts.get(model));
    });
  });

  describe('.unsaved', function () {
    it('should return drafts for unsaved annotations', function () {
      var model = {};
      drafts.update(model, {text: 'bar'});
      assert.deepEqual(drafts.unsaved(), [model]);
    });

    it('should not return drafts for saved annotations', function () {
      var model = {id: 'foo'};
      drafts.update(model, {text: 'baz'});
      assert.deepEqual(drafts.unsaved(), []);
    });
  });
});
