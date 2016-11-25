"""
Custom Pyramid view predicates.

Functions suitable for being passed to Pyramid view config's custom_predicates
argument.

"""


def has_read_permission(info, request):
    return request.has_permission('read')
