# -*- coding: utf-8 -*-
import colander
import deform

from pyramid import httpexceptions
from pyramid import security
from pyramid.config import not_
from pyramid.view import view_config, view_defaults
from sqlalchemy import or_

from h import form
from h import i18n
from h import models
from h import paginator
from h.accounts.schemas import CSRFSchema
from h.groups import schemas
from h.models.group import GroupFactory
from h.models.user import User, UserFactory
from jinja2 import Markup

_ = i18n.TranslationString


@view_config(route_name='admin_groups',
             request_method='GET',
             renderer='h:templates/admin/groups.html.jinja2',
             permission='admin_groups')
@paginator.paginate_query
def groups_index(context, request):
    return request.db.query(models.Group).order_by(models.Group.created.desc())


@view_defaults(route_name='admin_groups_create',
               renderer='h:templates/admin/groups_create.html.jinja2',
               permission='admin_groups',
               effective_principals=security.Authenticated)
class AdminGroupCreateController(object):
    """
    Controller for feature that lets user create a new group
    """

    def __init__(self, request):
        self.request = request

        self.schema = schemas.admin_group_create_schema().bind(
            request=self.request)

        submit = deform.Button(title=_('Create a new group'),
                               css_class='primary-action-btn '
                                         'admin-group-create-form__submit-btn '
                                         'js-create-group-create-btn')
        self.form = request.create_form(self.schema,
                                        formid='admin-group-create-form',
                                        css_class='admin-group-create-form__form',
                                        buttons=(submit,))

    @view_config(request_method='GET')
    def get(self):
        """Render the form for creating a new group."""
        return self._template_data()

    @view_config(request_method='POST')
    def post(self):
        """Respond to a submission of the create group form."""
        def on_success(appstruct):
            groups_service = self.request.find_service(name='group')
            group = groups_service.create(
                name=appstruct['name'],
                authority=self.request.authority,
                description=appstruct.get('description'),
                userid=self.request.authenticated_userid,
                type_=appstruct['group_type'])
            group_url = self.request.route_path('group_read',
                                                pubid=group.pubid,
                                                slug=group.slug)
            self.request.session.flash(Markup(
                'Group Created <a href="{url}">{url}</a>'.format(url=group_url)), queue='success')
            return httpexceptions.HTTPSeeOther(self.request.url)

        def on_failure(exception):
            return self._template_data()

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=on_failure,
            flash=False)

    def _template_data(self):
        """Return the data needed to render this controller's page."""
        return {'form': self.form.render()}


@view_defaults(route_name='admin_group_members',
               renderer='h:templates/admin/groups_members.html.jinja2',
               permission='admin_groups',
               effective_principals=security.Authenticated)
class AdminGroupMembersController(object):
    """
    Controller for feature that lets user create a new group
    """

    def __init__(self, request):
        self.request = request
        self.schema = self._add_member_schema.bind(request=self.request)
        self.form = request.create_form(self.schema,
                                        appstruct=dict(
                                            pubid=self.request.context.pubid),
                                        formid='admin-group-add-member-form',
                                        css_class='admin-group-add-member-form__form',
                                        buttons=(deform.Button(
                                            title=_(
                                                'Add Member to Group'),
                                            css_class='primary-action-btn '
                                            'admin-group-add-member-form__submit-btn '
                                            'js-group-add-member-btn'),))

    @view_config(request_method='GET')
    def get(self):
        """Render the existing members"""
        context = self._template_data()
        return context

    @view_config(request_method='POST')
    def post(self):
        """Respond to a submission of the create group form."""
        def on_success(appstruct):
            group = GroupFactory(self.request)[appstruct['pubid']]
            user = self._query_user(appstruct)
            assert user
            groups_service = self.request.find_service(name='group')
            groups_service.member_join(group, user.userid)
            self.request.session.flash('Added {user} to group'.format(
                user=user.username), queue='success')
            return httpexceptions.HTTPSeeOther(self.request.url)

        def on_failure(exception):
            return self._template_data()

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=on_failure,
            flash=False)

    def _template_data(self):
        @paginator.paginate_query
        def get_paging_context(group, request):
            query = request.db.query(models.User).filter(
                models.User.groups.contains(group))
            return query
        context = get_paging_context(self.request.context, self.request)
        context.update(dict(group=self.request.context,
                            add_member_form=self.form.render()))
        return context

    def _query_user(self, form_values):
        group_filters = dict([field, form_values[field]] for field in (
            'username', 'email') if form_values.get(field))
        user = self.request.db.query(User).filter(or_(
            *[getattr(User, field) == form_values for [field, form_values] in group_filters.items()])).one()
        return user

    @property
    def _add_member_schema(self):
        controller = self

        class AddMemberSchema(CSRFSchema):
            username = colander.SchemaNode(
                colander.String(),
                missing=None,
                name='username',
                title=_("Username"),
                widget=deform.widget.TextInputWidget(),)
            email = colander.SchemaNode(
                colander.String(),
                missing=None,
                name='email',
                title=_("email"),
                widget=deform.widget.TextInputWidget(),)
            pubid = colander.SchemaNode(
                colander.String(),
                name='pubid',
                widget=deform.widget.HiddenWidget(),)

            def validator(self, form, value):
                group = GroupFactory(controller.request)[value['pubid']]
                if value.get('username') and value.get('email'):
                    err = colander.Invalid(
                        form, 'Provide one of username or email, but not both')
                    err['username'] = 'not allowed with email'
                    err['email'] = 'not allowed with username'
                    raise err
                user = controller._query_user(value)
                if not user:
                    err = colander.Invalid(form)
                    err['username'] = "User not found"
                    raise err

        schema = AddMemberSchema()

        return schema
