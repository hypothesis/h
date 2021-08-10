import pytest

from h.views.api.helpers import links


class TestServiceLink:
    @pytest.mark.parametrize(
        "name,route_name,method,description,expected_method",
        [
            ("Create Foo", "foo.create", "POST", None, "POST"),
            ("Create Foo", "foo.create", ("POST", "PATCH"), None, "POST"),
            ("Create Foo", "foo.create", "GET", "Forever and a Day", "GET"),
        ],
    )
    def test_primary_method_returns_correct_HTTP_method(
        self, name, route_name, method, description, expected_method
    ):
        assert (
            links.ServiceLink(name, route_name, method, description).primary_method()
            == expected_method
        )


class TestRegisterLink:
    def test_it_creates_attrs_on_registry_if_not_present(
        self, versions, pyramid_config
    ):
        links.register_link(_service_link(), versions, pyramid_config.registry)

        assert hasattr(pyramid_config.registry, "api_links")
        assert "v1" in pyramid_config.registry.api_links
        assert "v2" in pyramid_config.registry.api_links

    def test_it_registers_link_for_every_version(self, versions, pyramid_config):
        link = _service_link()

        links.register_link(link, versions, pyramid_config.registry)

        assert link in pyramid_config.registry.api_links["v1"]
        assert link in pyramid_config.registry.api_links["v2"]

    def test_it_does_not_register_link_for_unsupported_versions(
        self, versions, pyramid_config
    ):
        first_service = _service_link()
        second_service = _service_link("doodad")

        links.register_link(first_service, versions, pyramid_config.registry)
        links.register_link(second_service, ["v1"], pyramid_config.registry)

        assert first_service in pyramid_config.registry.api_links["v2"]
        assert second_service not in pyramid_config.registry.api_links["v2"]


# TODO: Fix these tests
# class TestFormatNestedLinks:
#     def test_it_formats_link_objects_as_dicts(self, templater):
#         link = _service_link(name="flat")
#
#         formatted = links.format_nested_links([link], "v1", templater)
#
#         assert "flat" in formatted
#         assert formatted["flat"] == {
#             "method": link.primary_method(),
#             "url": templater.route_template(link.route_name),
#             "desc": link.description,
#         }
#
#     def test_it_nests_links_based_on_service_name_split_on_periods(self, templater):
#         api_links = [
#             _service_link(name="1"),
#             _service_link(name="1.2"),
#             _service_link(name="1.2.3"),
#             _service_link(name="1.2.A"),
#             _service_link(name="1.B"),
#         ]
#
#         formatted = links.format_nested_links([api_links], "v1", templater)
#
#         assert "1" in formatted
#         assert "2" in formatted["1"]
#         assert "B" in formatted["1"]
#         assert "3" in formatted["1"]["2"]
#         assert "A" in formatted["1"]["2"]

# @pytest.fixture
# def templater():
#     return mock.create_autospec(AngularRouteTemplater, spec_set=True, instance=True)


def _service_link(name="api.example_service"):  # pylint:disable=unused-argument
    return links.ServiceLink(
        name="name",
        route_name="api.example_service",
        method="POST",
        description="Create a new Foo",
    )


@pytest.fixture
def versions():
    return ["v1", "v2"]
