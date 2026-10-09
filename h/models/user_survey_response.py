from enum import StrEnum

import sqlalchemy as sa

from h.db import Base


class Survey(StrEnum):
    """A survey shown in the client's sidebar whose answers h records."""

    EDU_ROLE = "edu_role"


class EduRoleSurveyResponse(StrEnum):
    """A user's answer to the EDU role survey shown in the client's sidebar.

    Recorded so we only ask once. "dismissed" is a first-class answer, not an
    absence of one: the survey has to be dismissable to comply with GDPR, and a
    dismissal stops us asking again just like a yes or a no does.
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

    #: When this answer was last sent to HubSpot. Written by the daily HubSpot
    #: sync, and NULL until that sync exists.
    hubspot_synced_at = sa.Column(sa.DateTime(), nullable=True)

    def __repr__(self):
        return f"{self.__class__.__name__}(user_id={self.user_id!r}, survey={self.survey!r}, response={self.response!r})"
