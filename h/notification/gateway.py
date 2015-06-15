# -*- coding: utf-8 -*-
import re
from h.accounts import models


def user_name(user):
    return re.search(r'^acct:([^@]+)', user).group(1)


def user_profile_url(request, user):
    username = user_name(user)
    return request.application_url + '/u/' + username


def standalone_url(request, annotation_id):
    return request.application_url + '/a/' + annotation_id


def get_user_by_name(request, username):
    return models.User.get_by_username(username)


def includeme(config):
    pass
