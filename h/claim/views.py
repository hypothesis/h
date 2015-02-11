from pyramid.view import view_config


@view_config(
    route_name='claim_account',
    renderer='h:claim/templates/claim_account.html')
def claim_account(context, request):
    return {}


def includeme(config):
    config.add_route('claim_account', '/claim_account')
    config.scan(__name__)
