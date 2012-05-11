var $, Hypothesis
(function () {
  return new Hypothesis($('#content'), {
    Auth: {
      tokenUrl: '${request.route_url("token")}'
    },
    Store: {
      prefix: '${request.route_url("api", subpath="")}'
    }
  })
})()
