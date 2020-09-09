import pytest

from h.views.api.helpers import media_types


class TestMediaTypeForVersion:
    @pytest.mark.parametrize(
        "version,expected",
        [
            ("v1", "application/vnd.hypothesis.v1+json"),
            ("elephant", "application/vnd.hypothesis.elephant+json"),
        ],
    )
    def test_it_formats_version_into_media_type_string(self, version, expected):
        assert media_types.media_type_for_version(version) == expected

    @pytest.mark.parametrize(
        "version,subtype,expected",
        [
            ("v1", "json", "application/vnd.hypothesis.v1+json"),
            ("elephant", "json", "application/vnd.hypothesis.elephant+json"),
            ("v2", "json.ld", "application/vnd.hypothesis.v2+json.ld"),
            ("v3", "whatever", "application/vnd.hypothesis.v3+whatever"),
        ],
    )
    def test_it_appends_subtype_when_provided(self, version, subtype, expected):
        assert media_types.media_type_for_version(version, subtype) == expected


class TestValidMediaTypes:
    def test_it_returns_list_containing_version_types(self):
        assert media_types.valid_media_types() == [
            "*/*",
            "application/json",
            "application/vnd.hypothesis.v1+json",
            "application/vnd.hypothesis.v2+json",
        ]


class TestVersionMediaTypes:
    def test_it_returns_media_types_for_versions(self):
        assert media_types.version_media_types(["foo", "bar"]) == [
            "application/vnd.hypothesis.foo+json",
            "application/vnd.hypothesis.bar+json",
        ]

    def test_it_returns_all_known_versions_if_versions_is_None(self):
        assert media_types.version_media_types() == [
            "application/vnd.hypothesis.v1+json",
            "application/vnd.hypothesis.v2+json",
        ]
