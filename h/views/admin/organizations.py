from markupsafe import Markup
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from sqlalchemy import func

from h import form, i18n, models, paginator
from h.models.organization import Organization
from h.schemas.forms.admin.organization import OrganizationSchema
from h.security import Permission

_ = i18n.TranslationString


@view_config(
    route_name="admin.organizations",
    request_method="GET",
    renderer="h:templates/admin/organizations.html.jinja2",
    permission=Permission.AdminPage.LOW_RISK,
)
@paginator.paginate_query
def index(_context, request):
    q_param = request.params.get("q")

    filter_terms = []
    if q_param:
        filter_terms.append(func.lower(Organization.name).like(f"%{q_param.lower()}%"))

    return (
        request.db.query(Organization)
        .filter(*filter_terms)
        .order_by(Organization.created.desc())
    )


@view_defaults(
    route_name="admin.organizations_create",
    renderer="h:templates/admin/organizations_create.html.jinja2",
    permission=Permission.AdminPage.LOW_RISK,
)
class OrganizationCreateController:
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
            organization = Organization(authority=authority, name=name, logo=logo)

            self.request.db.add(organization)
            self.request.session.flash(
                # pylint:disable=consider-using-f-string
                Markup(_("Created new organization {}".format(name))),
                "success",
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
    permission=Permission.AdminPage.LOW_RISK,
    renderer="h:templates/admin/organizations_edit.html.jinja2",
)
class OrganizationEditController:
    def __init__(self, context, request):
        self.organization = context.organization
        self.request = request
        self.schema = OrganizationSchema().bind(request=request)
        self.form = request.create_form(self.schema, buttons=(_("Save"),))
        self._update_appstruct()

    @view_config(request_method="GET")
    def read(self):
        return self._template_context()

    @view_config(request_method="POST", route_name="admin.organizations_delete")
    def delete(self):
        # Prevent deletion while the organization has associated groups.
        group_count = (
            self.request.db.query(models.Group)
            .filter_by(organization=self.organization)
            .count()
        )
        if group_count > 0:
            self.request.response.status_int = 400
            self.request.session.flash(
                _(
                    # pylint:disable=consider-using-f-string
                    "Cannot delete organization because it is associated with {} groups".format(
                        group_count
                    )
                ),
                "error",
            )
            return self._template_context()

        # Delete the organization.
        self.request.db.delete(self.organization)
        self.request.session.flash(
            _(
                # pylint:disable=consider-using-f-string
                "Successfully deleted organization %s" % (self.organization.name),
                "success",
            )
        )
        return HTTPFound(location=self.request.route_path("admin.organizations"))

    @view_config(request_method="POST")
    def update(self):
        org = self.organization

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
        org = self.organization
        self.form.set_appstruct(
            {"authority": org.authority, "logo": org.logo or "", "name": org.name}
        )

    def _template_context(self):
        delete_url = None
        if not self.organization.is_default:
            delete_url = self.request.route_url(
                "admin.organizations_delete", pubid=self.organization.pubid
            )
        return {"form": self.form.render(), "delete_url": delete_url}
