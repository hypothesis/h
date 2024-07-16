def userid_from_identity(policy, request):
    if (identity := policy.identity(request)) and identity.user:
        return identity.user.userid

    return None
