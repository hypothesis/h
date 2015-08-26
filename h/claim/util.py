# -*- coding: utf-8 -*-
def generate_claim_token(request, userid):
    return request.registry.claim_serializer.dumps({'userid': userid})


def generate_claim_url(request, userid):
    ''' Generates a url that a user can visit to claim their account. '''
    token = generate_claim_token(request, userid)
    return request.route_url('claim_account', token=token)


def includeme(config):
    pass
