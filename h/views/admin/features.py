from pyramid import httpexceptions
from pyramid.view import view_config

from h import models, paginator
from h.i18n import TranslationString as _
from h.security import Permission


@view_config(
    route_name="admin.features",
    request_method="GET",
    renderer="h:templates/admin/features.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
)
def features_index(request):
    features = sorted(models.Feature.all(request.db), key=lambda f: f.name)

    return {
        "features": features,
        "cohorts": request.db.query(models.FeatureCohort).all(),
    }


@view_config(
    route_name="admin.features",
    request_method="POST",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def features_save(request):  # pragma: no cover
    for feat in models.Feature.all(request.db):
        for attr in ["everyone", "first_party", "admins", "staff"]:
            val = request.POST.get(f"{feat.name}[{attr}]")
            if val == "on":
                setattr(feat, attr, True)
            else:
                setattr(feat, attr, False)
        for cohort in request.db.query(models.FeatureCohort).all():
            val = request.POST.get(f"{feat.name}[cohorts][{cohort.name}]")
            if val == "on":
                if cohort not in feat.cohorts:
                    feat.cohorts.append(cohort)
            elif cohort in feat.cohorts:
                feat.cohorts.remove(cohort)

    request.session.flash(_("Changes saved."), "success")
    return httpexceptions.HTTPSeeOther(location=request.route_url("admin.features"))


@view_config(
    route_name="admin.cohorts",
    request_method="GET",
    renderer="h:templates/admin/cohorts.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
)
@paginator.paginate_query
def cohorts_index(_context, request):
    query = request.db.query(models.FeatureCohort)
    return query.order_by(models.FeatureCohort.name)


@view_config(
    route_name="admin.cohorts",
    request_method="POST",
    request_param="add",
    renderer="h:templates/admin/cohorts.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def cohorts_add(request):
    """Create a new feature cohort."""
    cohort_name = request.params["add"]
    cohort = models.FeatureCohort(name=cohort_name)
    request.db.add(cohort)

    url = request.route_url("admin.cohorts")
    return httpexceptions.HTTPSeeOther(url)


@view_config(
    route_name="admin.cohorts_edit",
    request_method="GET",
    renderer="h:templates/admin/cohorts_edit.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
)
def cohorts_edit(_context, request):
    id_ = request.matchdict["id"]
    cohort = request.db.get(models.FeatureCohort, id_)
    return {
        "cohort": cohort,
        "members": cohort.members,
        "default_authority": request.default_authority,
    }


@view_config(
    route_name="admin.cohorts_edit",
    request_method="POST",
    request_param="delete",
    permission=Permission.AdminPage.HIGH_RISK,
)
def cohorts_delete(_context, request):
    id_ = request.matchdict["id"]
    cohort = request.db.get(models.FeatureCohort, id_)
    request.db.delete(cohort)
    return httpexceptions.HTTPFound(location=request.route_url("admin.cohorts"))


@view_config(
    route_name="admin.cohorts_edit",
    request_method="POST",
    request_param="add",
    renderer="h:templates/admin/cohorts_edit.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def cohorts_edit_add(request):
    member_name = request.params["add"].strip()
    member_authority = request.params["authority"].strip()
    cohort_id = request.matchdict["id"]

    member = models.User.get_by_username(request.db, member_name, member_authority)
    if member is None:  # pragma: no cover
        request.session.flash(
            _(
                "User {member_name} with authority {authority} doesn't exist.".format(  # noqa: INT002, UP032
                    member_name=member_name, authority=member_authority
                )
            ),
            "error",
        )
    else:
        cohort = request.db.get(models.FeatureCohort, cohort_id)
        cohort.members.append(member)

    url = request.route_url("admin.cohorts_edit", id=cohort_id)
    return httpexceptions.HTTPSeeOther(url)


@view_config(
    route_name="admin.cohorts_edit",
    request_method="POST",
    request_param="remove",
    renderer="h:templates/admin/cohorts_edit.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def cohorts_edit_remove(request):
    member_userid = request.params["remove"]
    cohort_id = request.matchdict["id"]

    cohort = request.db.get(models.FeatureCohort, cohort_id)
    member = request.db.query(models.User).filter_by(userid=member_userid).first()
    try:
        cohort.members.remove(member)
    except ValueError:  # pragma: no cover
        request.session.flash(
            _(
                "User {member_userid} doesn't exist.".format(  # noqa: INT002, UP032
                    member_userid=member_userid
                )
            ),
            "error",
        )

    url = request.route_url("admin.cohorts_edit", id=cohort_id)
    return httpexceptions.HTTPSeeOther(url)
