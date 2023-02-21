from datetime import datetime

from h.services import EmailDigestsService
from h.views.api.config import api_config


@api_config(versions=["v2"], route_name="api.email_digests")
def email_digests(request):
    email_digests_service = request.find_service(EmailDigestsService)
    user_service = request.find_service(name="user")

    user = user_service.fetch(request.params["user"])
    since = datetime.fromisoformat(request.params["since"])
    until = datetime.fromisoformat(request.params["until"])

    result = email_digests_service.get(user, since, until)

    groups = {}
    for pubid, authority_provided_id, username, num_annotations in result:
        groups.setdefault(
            authority_provided_id,
            {"pubid": pubid, "authority_provided_id": authority_provided_id, "users": []},
        )
        groups[authority_provided_id]["users"].append(
            {"userid": username, "num_annotations": num_annotations}
        )

    return {"groups": list(groups.values())}
