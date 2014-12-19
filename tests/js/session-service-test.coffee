assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()

mockFlash = sandbox.spy()
mockDocumentHelpers = {absoluteURI: -> '/session'}

describe 'session', ->
  beforeEach module('h.session')

  beforeEach module ($provide, sessionProvider) ->
    $provide.value 'documentHelpers', mockDocumentHelpers
    $provide.value 'flash', mockFlash
    sessionProvider.actions =
      login:
        url: '/login'
        method: 'POST'
    return

  afterEach ->
    sandbox.restore()

  describe 'sessionService', ->
    $httpBackend = null
    session = null
    xsrf = null

    beforeEach inject (_$httpBackend_, _session_, _xsrf_) ->
      $httpBackend = _$httpBackend_
      session = _session_
      xsrf = _xsrf_

    describe '#<action>()', ->
      url = '/login'

      it 'should send an HTTP POST to the action', ->
        $httpBackend.expectPOST(url, code: 123).respond({})
        result = session.login(code: 123)
        $httpBackend.flush()

      it 'should invoke the flash service with any flash messages', ->
        response =
          flash:
            error: 'fail'
        $httpBackend.expectPOST(url).respond(response)
        result = session.login({})
        $httpBackend.flush()
        assert.calledWith mockFlash, 'error', 'fail'

      it 'should assign errors and status reasons to the model', ->
        response =
          model:
            userid: 'alice'
          errors:
            password: 'missing'
          reason: 'bad credentials'
        $httpBackend.expectPOST(url).respond(response)
        result = session.login({})
        $httpBackend.flush()
        assert.match result, response.model, 'the model is present'
        assert.match result.errors, response.errors, 'the errors are present'
        assert.match result.reason, response.reason, 'the reason is present'

      it 'should capture and send the xsrf token', ->
        token = 'deadbeef'
        headers =
          'Accept': 'application/json, text/plain, */*'
          'Content-Type': 'application/json;charset=utf-8'
          'X-XSRF-TOKEN': token
        model = {csrf: token}
        request = $httpBackend.expectPOST(url).respond({model})
        result = session.login({})
        $httpBackend.flush()
        assert.equal xsrf.token, token

        $httpBackend.expectPOST(url, {}, headers).respond({})
        session.login({})
        $httpBackend.flush()
