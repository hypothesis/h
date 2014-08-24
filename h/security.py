# -*- coding: utf-8 -*-
# Standard OpenID Connect scopes
OpenID = 'openid'
Profile = 'profile'
Email = 'email'
Address = 'address'
Phone = 'phone'
OfflineAccess = 'offline_access'

# Non-standard scopes
Account = 'https://hypothes.is/auth/account'
AccountR = 'https://hypothes.is/auth/account.readonly'

Annotations = 'https://hypothes.is/auth/annotations'
AnnotationsR = 'https://hypothes.is/auth/annotations.readonly'

WEB_SCOPES = [
    OpenID,
    Profile,
    Email,
    Account,
    Annotations,
]
