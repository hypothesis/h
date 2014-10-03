assert = chai.assert
sinon.assert.expose assert, prefix: null
sandbox = sinon.sandbox.create()

absoluteURI = (path) -> "https://example.com#{path}"

mockFlash = sandbox.spy()
mockDocumentHelpers = {absoluteURI}

describe 'session-service', ->
  beforeEach module('h')

  beforeEach module ($provide) ->
    $provide.value 'documentHelpers', mockDocumentHelpers
    $provide.value 'flash', mockFlash
    return

  afterEach ->
    sandbox.restore()

  describe 'session', ->
    $httpBackend = null
    session = null

    beforeEach inject (_$httpBackend_, _session_) ->
      $httpBackend = _$httpBackend_
      session = _session_

    it 'should have a HTTP GET "load" action', ->
      response =
        model:
          userid: 'alice'
      $httpBackend.expectGET(absoluteURI('/app')).respond(response)
      result = session.load()
      $httpBackend.flush()
      assert.equal result.userid, 'alice'

    describe '#<action>()', ->
      url = absoluteURI('/app?__formid__=login')

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
        headers =
          'Accept': 'application/json, text/plain, */*'
          'Content-Type': 'application/json;charset=utf-8'
          'X-CSRF-Token': 'deadbeef'
        csrf = 'deadbeef'
        model = {csrf}
        request = $httpBackend.expectPOST(url).respond({model})
        result = session.login({})
        $httpBackend.flush()
        $httpBackend.expectPOST(url, {}, headers).respond({model})
        session.login({})
        $httpBackend.flush()
