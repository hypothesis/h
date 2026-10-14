from enum import StrEnum

import sqlalchemy as sa

from h.db import Base


class Survey(StrEnum):
    """A survey shown in the client's sidebar whose answers h records."""

    EDU_ROLE = "edu_role"


class EduRoleSurveyResponse(StrEnum):
    """A user's answer to the EDU role survey shown in the client's sidebar.

    Any recorded answer stops the survey being shown. "dismissed" is a
    first-class answer, not an absence of one: the survey has to be dismissable
    to comply with GDPR, and a dismissal stops us asking again just like a yes
    or a no does.

    A dismissal can be replaced by a later answer, because product plans to
    re-run the survey for the people who dismissed it so they get to answer a
    second time. An "instructor" or "not_instructor" answer is never replaced:
    `UserService.update_preferences` upserts with a condition that only
    matches a dismissal.

    Nothing replaces a dismissal through the API yet, though. Until the re-ask
    lands, `h.session.show_edu_role_survey` stops asking once any answer is
    recorded, so `h.views.api.profile.update_preferences` drops a second
    answer before it reaches the upsert. Today the upsert's condition only
    settles two answers sent in the same instant.

    `UserSurveyResponse.responded_at` is written with the response beside it,
    so it is when *this* answer was recorded -- the first one, unless a later
    answer replaced a dismissal. It is not the date the user was first asked,
    nor necessarily the first time they replied.
    """

    INSTRUCTOR = "instructor"
    NOT_INSTRUCTOR = "not_instructor"
    DISMISSED = "dismissed"


class UserSurveyResponse(Base):
    """A user's answer to one of the surveys in `Survey`.

    One row per user and survey. A user with no row for a survey hasn't
    answered it, which is what makes that survey appear.
    """

    __tablename__ = "user_survey_response"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "survey", name="uq__user_survey_response__user_id__survey"
        ),
        sa.CheckConstraint(
            f"survey = '{Survey.EDU_ROLE}' AND response IN ("
            + ", ".join(f"'{response}'" for response in EduRoleSurveyResponse)
            + ")",
            name="validate_response",
        ),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    user_id = sa.Column(
        sa.Integer(), sa.ForeignKey("user.id", ondelete="cascade"), nullable=False
    )

    survey = sa.Column(sa.UnicodeText(), nullable=False)

    response = sa.Column(sa.UnicodeText(), nullable=False)

    #: When the user gave `response`.
    responded_at = sa.Column(sa.DateTime(), nullable=False)

    #: When this answer was last sent to HubSpot, by
    #: `HubSpotService.sync_edu_role_contacts`. NULL if it hasn't been sent.
    hubspot_synced_at = sa.Column(sa.DateTime(), nullable=True)

    def __repr__(self):
        return f"{self.__class__.__name__}(user_id={self.user_id!r}, survey={self.survey!r}, response={self.response!r})"
