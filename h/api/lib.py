from annotator import auth
from pyramid import security

from h import interfaces


def authenticator(request):
    fetcher = lambda key: get_consumer(request, key)
    return auth.Authenticator(fetcher)


def authorize(request, annotation, action, user=None):
    annotation = wrap_annotation(request, annotation)
    allowed = security.principals_allowed_by_permission(annotation, action)

    if user is None:
        principals = request.session.get('personas', [])
    else:
        principals = [user.id]

    if len(principals):
        principals.append(security.Authenticated)

    principals.append(security.Everyone)

    return set(allowed) & set(principals) != set()


def get_consumer(request, key):
    klass = request.registry.getUtility(interfaces.IConsumerClass)
    inst = klass.get_by_key(request, key)

    # Coerce types so elasticsearch doesn't choke on the UUIDs.
    # TODO: Can we add magic to h.models.GUID to take care of this?
    result = auth.Consumer(str(key))
    result.secret = str(inst.secret)
    result.ttl = inst.ttl

    return result


def wrap_annotation(request, annotation):
    """Wraps a dict as an instance of the registered Annotation model class.

    Arguments:
    - `annotation`: a dictionary-like object containing the model data
    """
    cls = request.registry.queryUtility(interfaces.IAnnotationClass)
    return cls(annotation)
