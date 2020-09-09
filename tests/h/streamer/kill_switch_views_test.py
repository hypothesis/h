from h.streamer.kill_switch_views import not_found


def test_not_found_view(pyramid_request):
    response = not_found(Exception(), pyramid_request)

    assert response.status_code == 429
    assert response.content_type is None
