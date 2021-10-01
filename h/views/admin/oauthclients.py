from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import NoResultFound, StatementError

from h import form, i18n
from h.models import AuthClient
from h.models.auth_client import GrantType, ResponseType
from h.schemas.auth_client import CreateAuthClientSchema, EditAuthClientSchema
from h.security import Permission, token_urlsafe

_ = i18n.TranslationString


def _response_type_for_grant_type(grant_type):
    if grant_type == GrantType.authorization_code:
        return ResponseType.code

    return None


@view_config(
    route_name="admin.oauthclients",
    renderer="h:templates/admin/oauthclients.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
)
def index(request):
    clients = request.db.query(AuthClient).order_by(AuthClient.name.asc()).all()
    return {"clients": clients}


@view_defaults(
    route_name="admin.oauthclients_create",
    permission=Permission.AdminPage.HIGH_RISK,
    renderer="h:templates/admin/oauthclients_create.html.jinja2",
)
class AuthClientCreateController:
    def __init__(self, request, secret_gen=token_urlsafe):
        self.request = request
        self.schema = CreateAuthClientSchema().bind(request=request)
        self.secret_gen = secret_gen
        self.form = request.create_form(self.schema, buttons=(_("Register client"),))

    @view_config(request_method="GET")
    def get(self):
        # Set useful defaults for new clients.
        self.form.set_appstruct(
            {
                "authority": self.request.default_authority,
                "grant_type": GrantType.authorization_code,
                "response_type": ResponseType.code,
                "trusted": False,
            }
        )
        return self._template_context()

    @view_config(request_method="POST")
    def post(self):
        def on_success(appstruct):
            grant_type = appstruct["grant_type"]

            if grant_type in [GrantType.jwt_bearer, GrantType.client_credentials]:
                secret = self.secret_gen()
            else:
                secret = None

            client = AuthClient(
                name=appstruct["name"],
                authority=appstruct["authority"],
                grant_type=appstruct["grant_type"],
                response_type=_response_type_for_grant_type(grant_type),
                secret=secret,
                trusted=appstruct["trusted"],
                redirect_uri=appstruct["redirect_url"],
            )

            self.request.db.add(client)
            self.request.db.flush()

            read_url = self.request.route_url("admin.oauthclients_edit", id=client.id)
            return HTTPFound(location=read_url)

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=self._template_context,
        )

    def _template_context(self):
        return {"form": self.form.render()}


@view_defaults(
    route_name="admin.oauthclients_edit",
    permission=Permission.AdminPage.HIGH_RISK,
    renderer="h:templates/admin/oauthclients_edit.html.jinja2",
)
class AuthClientEditController:
    def __init__(self, _context, request):
        self.request = request
        self.client = self._get_client(request)
        self.schema = EditAuthClientSchema().bind(request=request)
        self.form = request.create_form(self.schema, buttons=(_("Save"),))

    @view_config(request_method="GET")
    def read(self):
        self._update_appstruct()
        return self._template_context()

    @view_config(request_method="POST")
    def update(self):
        client = self.client

        def on_success(appstruct):
            grant_type = appstruct["grant_type"]

            client.authority = appstruct["authority"]
            client.grant_type = grant_type
            client.name = appstruct["name"]
            client.redirect_uri = appstruct["redirect_url"]
            client.response_type = _response_type_for_grant_type(grant_type)
            client.trusted = appstruct["trusted"]

            self._update_appstruct()

            return self._template_context()

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=self._template_context,
        )

    @view_config(request_method="POST", request_param="delete")
    def delete(self):
        self.request.db.delete(self.client)
        return HTTPFound(location=self.request.route_url("admin.oauthclients"))

    def _update_appstruct(self):
        client = self.client
        self.form.set_appstruct(
            {
                "authority": client.authority,
                "client_id": client.id,
                "client_secret": client.secret or "",
                "grant_type": client.grant_type,
                "name": client.name,
                "redirect_url": client.redirect_uri or "",
                "response_type": client.response_type,
                "trusted": client.trusted,
            }
        )

    def _template_context(self):
        return {"form": self.form.render()}

    @classmethod
    def _get_client(cls, request):
        client_id = request.matchdict.get("id")

        try:
            return request.db.query(AuthClient).filter_by(id=client_id).one()
        except (NoResultFound, StatementError) as err:
            # Statement errors happen if the id is invalid
            raise HTTPNotFound() from err
