import weakref

from pyramid.security import forget, remember, unauthenticated_userid

from h import interfaces


class WeakMemoizedProperty(property):
    """A property which memoizes the result of its getter

    Use this property when re-computing the value on each access is
    undesirable but reification of the value is inappropriate because a
    setter function is needed. All memoized values are cached using a weak
    reference to the owner object so there is no need to worry about cache
    cleanup.
    """
    memo = weakref.WeakKeyDictionary()

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable property")
        if obj not in self.memo:
            value = self.fget(obj)
            self.memo[obj] = value
        else:
            value = self.memo[obj]
        return value

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)
        self.memo[obj] = value

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)
        self.memo.pop(obj, None)


def get_user(request):
    userid = unauthenticated_userid(request)
    user_class = request.registry.queryUtility(interfaces.IUserClass)

    if userid is not None:
        return user_class.get_by_id(request, userid)

    return None


def set_user(request, user):
    # Must extract the id here since pyramid_tm will cause the database
    # session to be invalid by the time this runs.
    if user is not None:
        headers = remember(request, user.id)
    else:
        headers = forget(request)

    def _set_auth_headers(request, response):
        response.headerlist.extend(getattr(request, '_user_modified'))

    if not hasattr(request, '_user_modified'):
        request.add_response_callback(_set_auth_headers)

    setattr(request, '_user_modified', headers)


user_property = WeakMemoizedProperty(
    get_user,
    set_user,
    None,  # cannot be deleted
    """Stores the currently authenticated user object, automatically managing
    header manipulation when the value changes during request handling"""
)
