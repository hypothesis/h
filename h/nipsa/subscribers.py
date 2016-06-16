# -*- coding: utf-8 -*-


def transform_annotation(event):
    """Add a {"nipsa": True} field on annotations whose users are flagged."""
    annotation = event.annotation_dict
    nipsa_service = event.request.find_service(name='nipsa')
    if 'user' in annotation and nipsa_service.is_flagged(annotation['user']):
        annotation['nipsa'] = True
