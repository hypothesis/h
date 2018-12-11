# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from jinja2 import Markup
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound
from sqlalchemy import func

from h import form
from h import i18n
from h import models
from h.models.organization import Organization
from h import paginator
from h.schemas.forms.admin.organization import OrganizationSchema

_ = i18n.TranslationString


@view_config(
    route_name="admin.organizations",
    request_method="GET",
    renderer="h:templates/admin/organizations.html.jinja2",
    permission="admin_organizations",
)
@paginator.paginate_query
def index(context, request):
    q = request.params.get("q")

    filter_terms = []
    if q:
        filter_terms.append(
            func.lower(Organization.name).like("%{}%".format(q.lower()))
        )

    return (
        request.db.query(Organization)
        .filter(*filter_terms)
        .order_by(Organization.created.desc())
    )


@view_defaults(
    route_name="admin.organizations_create",
    renderer="h:templates/admin/organizations_create.html.jinja2",
    permission="admin_organizations",
)
class OrganizationCreateController(object):
    def __init__(self, request):
        self.schema = OrganizationSchema().bind(request=request)
        self.request = request
        self.form = request.create_form(
            self.schema, buttons=(_("Create organization"),)
        )

    @view_config(request_method="GET")
    def get(self):
        self.form.set_appstruct({"authority": self.request.default_authority})
        return self._template_context()

    @view_config(request_method="POST")
    def post(self):
        def on_success(appstruct):
            authority = appstruct["authority"]
            logo = appstruct["logo"]
            name = appstruct["name"]
            org = Organization(authority=authority, name=name, logo=logo)

            self.request.db.add(org)
            self.request.session.flash(
                Markup(_("Created new organization {}".format(name))), "success"
            )

            return HTTPFound(location=self.request.route_url("admin.organizations"))

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=self._template_context,
        )

    def _template_context(self):
        return {"form": self.form.render()}


@view_defaults(
    route_name="admin.organizations_edit",
    permission="admin_organizations",
    renderer="h:templates/admin/organizations_edit.html.jinja2",
)
class OrganizationEditController(object):
    def __init__(self, org, request):
        self.org = org
        self.request = request
        self.schema = OrganizationSchema().bind(request=request)
        self.form = request.create_form(self.schema, buttons=(_("Save"),))
        self._update_appstruct()

    @view_config(request_method="GET")
    def read(self):
        return self._template_context()

    @view_config(request_method="POST", route_name="admin.organizations_delete")
    def delete(self):
        org = self.org

        # Prevent deletion while the organization has associated groups.
        group_count = (
            self.request.db.query(models.Group).filter_by(organization=org).count()
        )
        if group_count > 0:
            self.request.response.status_int = 400
            self.request.session.flash(
                _(
                    "Cannot delete organization because it is associated with {} groups".format(
                        group_count
                    )
                ),
                "error",
            )
            return self._template_context()

        # Delete the organization.
        self.request.db.delete(org)
        self.request.session.flash(
            _("Successfully deleted organization %s" % (org.name), "success")
        )
        return HTTPFound(location=self.request.route_path("admin.organizations"))

    @view_config(request_method="POST")
    def update(self):
        org = self.org

        def on_success(appstruct):
            org.name = appstruct["name"]
            org.logo = appstruct["logo"]

            self._update_appstruct()

            return self._template_context()

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=self._template_context,
        )

    def _update_appstruct(self):
        org = self.org
        self.form.set_appstruct(
            {"authority": org.authority, "logo": org.logo or "", "name": org.name}
        )

    def _template_context(self):
        delete_url = None
        if self.org.pubid != "__default__":
            delete_url = self.request.route_url(
                "admin.organizations_delete", pubid=self.org.pubid
            )
        return {"form": self.form.render(), "delete_url": delete_url}
