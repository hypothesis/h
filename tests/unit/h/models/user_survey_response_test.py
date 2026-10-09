from datetime import datetime

import pytest
import sqlalchemy as sa
from sqlalchemy import exc

from h import models


class TestUserSurveyResponse:
    @pytest.mark.parametrize("response", ["instructor", "not_instructor", "dismissed"])
    def test_it_accepts_valid_edu_role_answers(self, db_session, user, response):
        db_session.add(self.survey_response(user, response=response))

        db_session.flush()

    @pytest.mark.parametrize("response", ["maybe", "INSTRUCTOR", ""])
    def test_it_rejects_invalid_edu_role_answers(self, db_session, user, response):
        # The CHECK constraint backs up the validation in UserService: this is
        # what catches a write that does not go through update_preferences.
        db_session.add(self.survey_response(user, response=response))

        with pytest.raises(exc.IntegrityError, match="validate_response"):
            db_session.flush()

    def test_it_rejects_unknown_surveys(self, db_session, user):
        db_session.add(self.survey_response(user, survey="other_survey"))

        with pytest.raises(exc.IntegrityError, match="validate_response"):
            db_session.flush()

    @pytest.mark.parametrize("column", ["user", "survey", "response", "responded_at"])
    def test_required_columns_cant_be_null(self, db_session, user, column):
        db_session.add(self.survey_response(user, **{column: None}))

        with pytest.raises(exc.IntegrityError, match="null value in column"):
            db_session.flush()

    def test_a_user_can_only_answer_a_survey_once(self, db_session, user):
        db_session.add_all(
            [
                self.survey_response(user, response="dismissed"),
                self.survey_response(user, response="instructor"),
            ]
        )

        with pytest.raises(
            exc.IntegrityError,
            match="uq__user_survey_response__user_id__survey",
        ):
            db_session.flush()

    def test_deleting_a_user_deletes_their_answers(self, db_session, user):
        db_session.add(self.survey_response(user))
        db_session.flush()

        # Delete through SQL rather than the session, so it's the foreign key's
        # ON DELETE CASCADE doing the work and not the ORM relationship.
        db_session.execute(sa.delete(models.User).where(models.User.id == user.id))

        assert not db_session.scalar(
            sa.select(sa.func.count()).select_from(models.UserSurveyResponse)
        )

    def test_repr(self):
        survey_response = models.UserSurveyResponse(
            user_id=1, survey="edu_role", response="dismissed"
        )

        assert (
            repr(survey_response)
            == "UserSurveyResponse(user_id=1, survey='edu_role', response='dismissed')"
        )

    def survey_response(self, user, /, **kwargs):
        kwargs = {
            "user": user,
            "survey": "edu_role",
            "response": "instructor",
            "responded_at": datetime(2026, 10, 14, 13, 2),  # noqa: DTZ001
            **kwargs,
        }
        return models.UserSurveyResponse(**kwargs)

    @pytest.fixture
    def user(self, factories):
        return factories.User()
