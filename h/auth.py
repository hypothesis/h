from annotator.auth import decode_token
from pyramid.authentication import SessionAuthenticationPolicy


class HybridAuthenticationPolicy(SessionAuthenticationPolicy):
    def effective_principals(self, request):
        base = super(HybridAuthenticationPolicy, self)
        effective_principals = base.effective_principals(request)

        if 'x-annotator-auth-token' in request.headers:
            token = request.headers['x-annotator-auth-token']
            userid = decode_token(token).get('userId')
            if userid:
                effective_principals.append(userid)

        return effective_principals
