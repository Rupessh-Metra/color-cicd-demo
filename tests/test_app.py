import re

import pytest

from app import app, color_for_build

HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello from CI/CD!" in response.data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_info_returns_build_details(client):
    data = client.get("/api/info").get_json()
    assert set(data) == {"build", "version", "color", "started"}
    assert HEX_COLOR.match(data["color"])


def test_color_is_a_valid_hex_value():
    for build in range(50):
        assert HEX_COLOR.match(color_for_build(build))


def test_each_new_build_gets_a_different_color():
    colors = [color_for_build(build) for build in range(1, 21)]
    assert len(set(colors)) == len(colors)


def test_bad_build_number_falls_back_safely():
    assert color_for_build("not-a-number") == color_for_build(0)
    assert color_for_build(None) == color_for_build(0)
