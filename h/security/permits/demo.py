if __name__ == "__main__":
    from h.models import Annotation, Group, User
    from h.models.group import ReadableBy
    from h.security.identity import Identity
    from h.security.permissions import Permission
    from h.security.permits import permits
    from h.traversal.annotation import AnnotationContext

    group = Group(readable_by=ReadableBy.members)
    annotation = Annotation(group=group, shared=True)
    user = User(groups=[group])

    identity = Identity(user=user)
    context = AnnotationContext(annotation=annotation, group=annotation.group)

    permits(identity, context, Permission.Annotation.READ)

    reps = 1000
    # reps = 1

    from datetime import datetime

    start = datetime.utcnow()

    permission_groups = (
        Permission.Annotation,
        Permission.Group,
        Permission.AdminPage,
        Permission.User,
        Permission.API,
        Permission.Profile,
    )

    for _ in range(reps):
        for permission_group in permission_groups:
            for permission in permission_group:
                allowed = permits(identity, context, permission)

    diff = datetime.utcnow() - start
    ms = diff.seconds * 1000 + diff.microseconds / 1000
    print(
        ms,
        "ms",
        ms / reps,
        "ms/item",
        ms * 1000 / reps,
        "us/item",
        reps / ms,
        "item/ms",
    )

    print(allowed)
