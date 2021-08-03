from h.cli.commands import annotation_id


class TestConvertFromURLSafe:
    def test_converts_from_url_safe_id(self, cli):
        result = cli.invoke(annotation_id.from_urlsafe, ["3jgSANNlEeebpLMf36MACw"])
        assert not result.exit_code
        assert result.output == "de381200-d365-11e7-9ba4-b31fdfa3000b\n"

    def test_fails_on_malformed_id(self, cli):
        result = cli.invoke(annotation_id.from_urlsafe, ["horse?"])
        assert result.exit_code
        assert not result.output


class TestConvertToURLSafe:
    def test_converts_to_url_safe_id(self, cli):
        result = cli.invoke(
            annotation_id.to_urlsafe, ["de381200-d365-11e7-9ba4-b31fdfa3000b"]
        )
        assert not result.exit_code
        assert result.output == "3jgSANNlEeebpLMf36MACw\n"

    def test_fails_on_malformed_id(self, cli):
        result = cli.invoke(annotation_id.to_urlsafe, ["horse?"])
        assert result.exit_code
        assert not result.output
