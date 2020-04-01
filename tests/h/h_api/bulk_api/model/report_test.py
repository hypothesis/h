from h.h_api.bulk_api.model.report import Report


class TestReport:
    def test_it(self):
        report = Report("id")

        assert report.id == "id"
        assert report.public_id == "id"

    def test_different_ids(self):
        report = Report("private_id", "public_id")

        assert report.id == "private_id"
        assert report.public_id == "public_id"
