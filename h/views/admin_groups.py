# -*- coding: utf-8 -*-
import colander
import deform
import re

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
from h.services.group import get_group_type, GROUP_TYPES

_ = i18n.TranslationString

admin_form_class = 'admin-form__form'


def admin_form_creator(request):
    """return a function that will create a form configured for the admin"""
    def create_form(*args, **kwargs):
        return request.create_form(*args, **kwargs)
    return create_form


def _get_group_type_description(
    group_type): return GROUP_TYPES[group_type]['description']


@view_config(route_name='admin_groups',
             request_method='GET',
             renderer='h:templates/admin/groups.html.jinja2',
             permission='admin_groups')
def groups_index(context, request):
    context = dict(get_group_type=get_group_type,
                   get_group_type_description=_get_group_type_description,)
    context.update(**paginator.paginate_query(lambda group, request: request.db.query(
        models.Group).order_by(models.Group.created.desc()))(context, request))
    return context


def admin_group_create_schema():
    schema = schemas.group_schema()
    schema.add(colander.SchemaNode(colander.String(),
                                   name='authority',
                                   title=_("Authority"),
                                   ))
    schema.add(colander.SchemaNode(colander.String(),
                                   name='group_type',
                                   title=_("Group Type"),
                                   validator=colander.OneOf(
                                       GROUP_TYPES.keys()),
                                   widget=deform.widget.SelectWidget(
        values=[
            [group_type, '{title} - {description}'.format(
                title=group_type.capitalize(), description=group_type_info['description'])]
            for [group_type, group_type_info]
            in GROUP_TYPES.items()
        ]
    )
    ))
    return schema


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
        self.schema = admin_group_create_schema().bind(request=self.request)

        submit = deform.Button(title=_('Create a new group'),
                               css_class='primary-action-btn '
                                         'admin-group-create-form__submit-btn '
                                         'js-create-group-create-btn')
        self.form = admin_form_creator(self.request)(
            self.schema,
            appstruct=dict(authority=self.request.authority),
            formid='admin-group-create-form',
            css_class=' '.join(
                [admin_form_class, 'admin-group-create-form__form']),
            buttons=(submit,))

    @view_config(request_method='GET')
    def get(self):
        """Render the form for creating a new group."""
        return self._template_data()

    @view_config(request_method='POST')
    def post(self):
        """Respond to a submission of the create group form."""
        def on_success(form_data):
            groups_service = self.request.find_service(name='group')
            group = groups_service.create(
                name=form_data['name'],
                authority=self.request.authority,
                description=form_data.get('description'),
                userid=self.request.authenticated_userid,
                type_=form_data['group_type'])
            group_url = self.request.route_path('admin_group_read',
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


class Username(colander.TupleSchema):
    username = colander.SchemaNode(
        colander.String(),
        name='username',
        title=_("Username"),)


class CSVScalarWidget(deform.widget.TextAreaCSVWidget):
    def _split(self, values_string):
        return re.split('[,\n ]', values_string)

    def serialize(self, field, cstruct, *args, **kwargs):
        # make tuples since that's
        cstruct_tuples = ((s,) for s in cstruct) if cstruct else cstruct
        return super(CSVScalarWidget, self).serialize(field, cstruct_tuples, *args, **kwargs)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        if not pstruct.strip():
            return colander.null
        entries = filter(bool, map(lambda s: s.strip(), self._split(pstruct)))
        return entries

    def handle_error(self, field, error):
        msgs = []
        if error.msg:
            field.error = error
        else:
            for e in error.children:
                msgs.append('value %s: %s' % (e.pos + 1, e[1]))
            field.error = colander.Invalid(field.schema, '\n'.join(msgs))


class UserIdentifier(colander.SchemaNode):
    name = 'user_identifier'

    def validator(self, *args, **kwargs):
        schema_node = self

        def does_user_exist(user_identifier):
            schema_node = self
            required_group = schema_node.bindings.get('group')
            fields = ('username', 'email')
            # any user where one of fields matches one of the user_identifiers
            # @TODO (bengo) filter by authority?
            request = self.bindings['request']
            user_identifiers_match = or_(
                *[getattr(User, field) == user_identifier for field in fields])
            has_group_authority = (
                models.User.authority == required_group.authority) if required_group else True
            users = request.db.query(User).filter(
                user_identifiers_match & has_group_authority).all()
            return users
        validate = colander.Function(
            does_user_exist, msg='User does not exist')
        return validate(*args, **kwargs)

    def schema_type(self):
        return colander.String()


def validate_pubid(node, value):
    return GroupFactory(node.bindings['request'])[value]


class AddGroupMemberSchema(CSRFSchema):
    pubid = colander.SchemaNode(
        colander.String(),
        name='pubid',
        widget=deform.widget.HiddenWidget(),
        validator=validate_pubid)

    def __init__(self, *args, **kwargs):
        if 'query_user' in kwargs:
            self._query_user = kwargs.pop('query_user')
        super(AddGroupMemberSchema, self).__init__(*args, **kwargs)

    def _query_user(self, query):
        raise NotImplementedError


class AddMultipleMembersSchema(AddGroupMemberSchema):
    user_identifiers = colander.SchemaNode(
        colander.Sequence(),
        UserIdentifier(),
        description='Enter one or more usernames and/or email addresses',
        widget=CSVScalarWidget())


class AddMemberByUsernameOrEmailSchema(AddGroupMemberSchema):
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

    def __init__(self, *args, **kwargs):
        super(AddMemberByUsernameOrEmailSchema, self).__init__(*args, **kwargs)

    def validator(self, form, value):
        request = form.bindings['request']
        group = GroupFactory(request)[value['pubid']]
        user_fields = ('username', 'email')
        user_query = dict([field, value[field]]
                          for field in user_fields)
        if all(user_query.values()):
            err = colander.Invalid(
                form, 'Provide one of {0}, but not both'.format(', '.join(user_fields)))
            for field, value in user_query.items():
                err[field] = 'not allowed with {0}'.format(
                    ', '.join(f for f in user_fields if f != field))
            raise err
        elif not any(user_query.values()):
            err = colander.Invalid(
                form, 'Provide one of {0}'.format(', '.join(user_fields)))
            raise err
        user = self._query_user(user_query)
        if not user:
            err = colander.Invalid(form)
            for field in [field for field, value in user_query.items() if value]:
                err[field] = 'user not found'
            raise err


class RemoveMemberSchema(CSRFSchema):
    userid = colander.SchemaNode(
        colander.String(),
        name='userid',
        widget=deform.widget.HiddenWidget(),)
    pubid = colander.SchemaNode(
        colander.String(),
        name='pubid',
        widget=deform.widget.HiddenWidget(),)

    def validator(self, form, value):
        request = form.bindings['request']
        group = GroupFactory(request)[value['pubid']]
        user = request.find_service(name='user').fetch(value['userid'])
        if group not in user.groups:
            exc = colander.Invalid(form)
            exc['user'] = 'there is no matching user in this group'
            raise exc


@view_defaults(route_name='admin_group_read',
               renderer='h:templates/admin/group_read.html.jinja2',
               permission='admin_groups',
               effective_principals=security.Authenticated)
class AdminGroupReadController(object):
    """
    Controller for feature that lets user create a new group
    """
    AddMemberFormSchema = AddMultipleMembersSchema

    def __init__(self, request):
        self.request = request

    @view_config(request_method='GET')
    def get(self):
        """Render the existing members"""
        context = self._template_data()
        return context

    @view_config(request_method='POST')
    def post(self):
        """Respond to a submission of the create group form."""

        form_for_formid = self._form_for_formid(
            self.request.POST['__formid__'])

        def on_success(form_data):
            form_kind = form_for_formid
            if isinstance(form_for_formid.schema, self.AddMemberFormSchema):
                group = GroupFactory(self.request)[form_data['pubid']]
                users = self._query_users(**form_data)
                assert users
                groups_service = self.request.find_service(name='group')

                def add_user(user):
                    assert user.authority == group.authority
                    groups_service.member_join(group, user.userid)
                    return user
                added_users = map(add_user, users)
                self.request.session.flash('Added {user} to group'.format(user=users[0].username if len(users) == 1 else '{num} users'.format(num=len(users))),
                                           queue='success')
                return httpexceptions.HTTPSeeOther(self.request.url)
            elif isinstance(form_for_formid.schema, RemoveMemberSchema):
                group = GroupFactory(self.request)[form_data['pubid']]
                user = self.request.find_service(
                    name='user').fetch(form_data['userid'])
                assert user
                groups_service = self.request.find_service(name='group')
                groups_service.member_leave(group, user.userid)
                self.request.session.flash('Removed {user} from group'.format(
                    user=user.username), queue='success')
                return httpexceptions.HTTPSeeOther(self.request.url)
            raise ValueError('unexpected form kind in on_success')

        def on_failure(exception):
            kwargs = dict()
            if isinstance(form_for_formid.schema, self.AddMemberFormSchema):
                kwargs.update(add_member_form=form_for_formid)
            return self._template_data(**kwargs)

        return form.handle_form_submission(
            self.request,
            form_for_formid,
            on_success=on_success,
            on_failure=on_failure,
            flash=False)

    def _template_data(self, add_member_form=None):
        @paginator.paginate_query
        def get_paging_context(group, request):
            query = request.db.query(models.User).filter(
                models.User.groups.contains(group))
            return query
        context = get_paging_context(self.request.context, self.request)
        context.update(dict(group=self.request.context,
                            get_group_type=get_group_type,
                            get_group_type_description=_get_group_type_description,
                            add_member_form=add_member_form or self._create_add_member_form(),
                            remove_member_form=self._create_remove_member_form,))
        return context

    def _query_user(self, form_data):
        group_filters = dict([field, form_data[field]] for field in (
            'username', 'email') if form_data.get(field))
        user = self.request.db.query(User).filter(or_(
            *[getattr(User, field) == form_data for [field, form_data] in group_filters.items()])).first()
        return user

    def _query_users(self, **kwargs):
        if 'user_identifiers' not in kwargs:
            return self._query_user(self, kwargs)
        user_identifiers = kwargs.get('user_identifiers', [])
        fields = ('username', 'email')
        # any user where one of fields matches one of the user_identifiers
        # @TODO (bengo) filter by authority?
        users_query = self.request.db.query(User).filter(or_(
            *[getattr(User, field) == value for field in fields for value in user_identifiers])).all()
        return users_query

    def _remove_member_formid(self):
        return 'admin-group-remove-member-form'

    def _form_for_formid(self, formid):
        if re.search(r'^admin-group-remove-member-form', formid):
            # it's a remove form
            return self._create_remove_member_form()
        elif re.search(r'^admin-group-add-member-form', formid):
            return self._create_add_member_form()
        raise ValueError(
            "don't know how to create form for formid {0}".format(formid))

    def _create_add_member_form(self,
                                formid='admin-group-add-member-form',
                                css_class=' '.join(
                                    [admin_form_class, 'admin-group-add-member-form__form']),
                                buttons=None):
        schema = self._add_member_schema
        form = admin_form_creator(self.request)(
            schema,
            appstruct=dict(
                pubid=self.request.context.pubid),
            formid=formid,
            css_class=css_class,
            buttons=buttons or (deform.Button(
                title=_(
                    'Add Member to Group'),
                css_class='primary-action-btn '
                'admin-group-add-member-form__submit-btn '
                'js-group-add-member-btn'),))
        return form

    def _create_remove_member_form(self, group=None, userid=None):
        schema = self._remove_member_schema
        appstruct = dict()
        if group:
            appstruct.update(pubid=group.pubid)
        if userid:
            appstruct.update(userid=userid)
        form = admin_form_creator(self.request)(
            schema,
            appstruct=appstruct,
            formid=self._remove_member_formid(),
            css_class=' '.join(
                [admin_form_class, 'admin-group-remove-member-form__form']),
            buttons=[
                deform.Button(
                    title=_('Remove'),
                    css_class=' '.join(['primary-action-btn ',
                                        'admin-group-remove-member-form__submit-btn']),)
            ],)
        return form

    @property
    def _remove_member_schema(self):
        schema = RemoveMemberSchema().bind(request=self.request)
        return schema

    @property
    def _add_member_schema(self):
        schema = self.AddMemberFormSchema().bind(request=self.request,
                                                 group=self.request.context)
        return schema
