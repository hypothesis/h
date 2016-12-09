# coding=utf8
from pyramid import httpexceptions as exc
from pyramid.view import view_config
from pyramid import renderers
from pyramid import httpexceptions
from h import i18n
from h import models
from elasticsearch import helpers as es_helpers


_ = i18n.TranslationString


@view_config(route_name='manager_create',
             request_method='POST')
def create(request):
    """ create manager. """
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    try:
        json_body = request.json_body
    except ValueError as err:
        raise Exception(
            _('Could not parse request body as JSON: {message}'.format(
                message=err.message)))

    if not isinstance(json_body, dict):
        raise Exception(
            _('Request JSON body must have a top-level object'))

    url = unicode(json_body.get('url') or '')
    if not url:
        raise exc.HTTPNotFound()

    manager = models.Follower(
        user=request.authenticated_user, url=url)
    request.db.add(manager)
    request.db.flush()

    return exc.HTTPNoContent()


@view_config(route_name='manager_delete',
             request_method='DELETE')
def delete(request):
    manager_id = request.params.get('id')
    manager = models.Manager.get_by_id(manager_id)

    if manager is None:
        request.session.flash(
            'Cannot find manager with id %s' % manager_id, 'error')
    else:
        try:
            request.db.delete(manager)
            request.session.flash(
                'Successfully deleted manager id %s' % manager_id, 'success')
        except Exception as e:
            request.session.flash(str(e), 'error')

    return httpexceptions.HTTPFound(
        location=request.route_path('admin_users'))


@view_config(route_name='manager_annotation',
             request_method='GET')
def get_annotations(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    annotations = []

    managers = models.Manager.get_by_user(request.authenticated_user)

    for m in managers:
        query = {
            'filtered': {
                'filter': {'term': {'_target_uri_normalized': m.url}},
                'query': {'match_all': {}}
            }
        }
        annotations.extend(list(es_helpers.scan(client=request.es.conn, query={'query': query})))

    return renderers.render_to_response(
        renderer_name='h:templates/managers/manager.html.jinja2',
        value=annotations, request=request)



def includeme(config):
    config.add_route('manager_create', '/manager/new')
    config.add_route('manager_delete', '/mangaer/delete')
    config.add_route('manager_annotation', '/manager/annotation')
    config.scan(__name__)
