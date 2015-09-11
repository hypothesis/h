{module, inject} = angular.mock

describe 'h:permissions', ->
  sandbox = null
  fakeSession = null

  before ->
    angular.module('h', [])
    .service('permissions', require('../permissions'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakeSession = {
      state: {
        userid: 'acct:flash@gordon'
      }
    }

    $provide.value 'session', fakeSession
    return

  afterEach ->
    sandbox.restore()


  describe 'permissions service', ->
    permissions = null

    beforeEach inject (_permissions_) ->
      permissions = _permissions_

    it 'private call fills all permissions with auth.user', ->
      perms = permissions.private()
      assert.equal(perms.read[0], 'acct:flash@gordon')
      assert.equal(perms.update[0], 'acct:flash@gordon')
      assert.equal(perms.delete[0], 'acct:flash@gordon')
      assert.equal(perms.admin[0], 'acct:flash@gordon')

    it 'public call fills the read property with group:__world__', ->
      perms = permissions.public()
      assert.equal(perms.read[0], 'group:__world__')
      assert.equal(perms.update[0], 'acct:flash@gordon')
      assert.equal(perms.delete[0], 'acct:flash@gordon')
      assert.equal(perms.admin[0], 'acct:flash@gordon')

    it 'public call fills the read property with group:foo if passed "foo"', ->
      perms = permissions.public("foo")
      assert.equal(perms.read[0], 'group:foo')
      assert.equal(perms.update[0], 'acct:flash@gordon')
      assert.equal(perms.delete[0], 'acct:flash@gordon')
      assert.equal(perms.admin[0], 'acct:flash@gordon')

    describe 'isPublic', ->
      it 'isPublic() true if the read permission has group:__world__ in it', ->
        permission = {
            read: ['group:__world__', 'acct:angry@birds.com']
        }
        assert.isTrue(permissions.isPublic(permission))

      it 'isPublic() false otherwise', ->
        permission = {
            read: ['acct:angry@birds.com']
        }

        assert.isFalse(permissions.isPublic(permission))
        permission.read = []
        assert.isFalse(permissions.isPublic(permission))
        permission.read = ['one', 'two', 'three']
        assert.isFalse(permissions.isPublic(permission))

    describe 'isPrivate', ->
      it 'returns true if the given user is in the permissions', ->
        user = 'acct:angry@birds.com'
        permission = {read: [user]}
        assert.isTrue(permissions.isPrivate(permission, user))

      it 'returns false if another user is in the permissions', ->
        users = ['acct:angry@birds.com', 'acct:angry@joe.com']
        permission = {read: users}
        assert.isFalse(permissions.isPrivate(permission, 'acct:angry@birds.com'))

      it 'returns false if different user in the permissions', ->
        user = 'acct:angry@joe.com'
        permission = {read: ['acct:angry@birds.com']}
        assert.isFalse(permissions.isPrivate(permission, user))

    describe 'permits', ->
      it 'returns true when annotation has no permissions', ->
        annotation = {}
        assert.isTrue(permissions.permits(null, annotation, null))

      it 'returns false for unknown action', ->
        annotation = {permissions: permissions.private()}
        action = 'Hadouken-ing'
        assert.isFalse(permissions.permits(action, annotation, null))

      it 'returns true if user different, but permissions has group:__world__', ->
        annotation = {permissions: permissions.public()}
        annotation.permissions.read.push 'acct:darthsidious@deathstar.emp'
        user = 'acct:darthvader@deathstar.emp'
        assert.isTrue(permissions.permits('read', annotation, user))

      it 'returns true if user is in permissions[action] list', ->
        annotation = {permissions: permissions.private()}
        user = 'acct:rogerrabbit@toonland'
        annotation.permissions.read.push user
        assert.isTrue(permissions.permits('read', annotation, user))

      it 'returns false if the user name is missing from the list', ->
        annotation = {permissions: permissions.private()}
        user = 'acct:rogerrabbit@toonland'
        assert.isFalse(permissions.permits('read', annotation, user))
