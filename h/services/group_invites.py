from h.models import GroupInvite


class GroupInvitesService:
    def __init__(self, db):
        self._db = db

    def list(self, group: Group, offset=None, limit=None):
        query = select(GroupInvite).where(GroupInvite.group == group)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return self.db.scalars(query)


def factory(_context, request):
    return GroupInvitesService(db=request.db)
