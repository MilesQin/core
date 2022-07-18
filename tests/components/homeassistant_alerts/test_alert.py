"""Test the resolution center creates issues from alerts."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest

from homeassistant.components.homeassistant_alerts.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import assert_lists_same, async_fire_time_changed, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


@pytest.mark.parametrize(
    "ha_version, expected_alerts",
    (
        (
            "2022.7.0",
            [
                ("aladdin_connect.markdown", "aladdin_connect"),
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("hive_us.markdown", "hive"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
        ),
        (
            "2022.8.0",
            [
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("hive_us.markdown", "hive"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
        ),
        (
            "2021.10.0",
            [
                ("aladdin_connect.markdown", "aladdin_connect"),
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
        ),
    ),
)
async def test_alerts(
    hass: HomeAssistant,
    hass_ws_client,
    aioclient_mock: AiohttpClientMocker,
    ha_version,
    expected_alerts,
) -> None:
    """Test creating issues based on alerts."""

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=load_fixture("alerts_1.json", "homeassistant_alerts"),
    )

    activated_components = (
        "aladdin_connect",
        "darksky",
        "hikvision",
        "hikvisioncam",
        "hive",
        "homematicip_cloud",
        "logi_circle",
        "neato",
        "nest",
        "senseme",
        "sochain",
    )
    for domain in activated_components:
        hass.config.components.add(domain)

    with patch(
        "homeassistant.components.homeassistant_alerts.alert.__version__",
        ha_version,
    ):
        assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "resolution_center/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            {
                "breaks_in_ha_version": None,
                "dismissed": False,
                "dismissed_version": None,
                "domain": "homeassistant_alerts",
                "is_fixable": False,
                "issue_id": f"{alert}_{integration}",
                "learn_more_url": f"https://alerts.home-assistant.io/#{alert}",
                "severity": "warning",
                "translation_key": "alert",
                "translation_placeholders": {"integration": integration},
            }
            for alert, integration in expected_alerts
        ]
    }


@pytest.mark.parametrize(
    "ha_version, fixture, expected_alerts",
    (
        (
            "2022.7.0",
            "alerts_no_url.json",
            [
                ("dark_sky.markdown", "darksky"),
            ],
        ),
        (
            "2022.7.0",
            "alerts_no_integrations.json",
            [
                ("dark_sky.markdown", "darksky"),
            ],
        ),
        (
            "2022.7.0",
            "alerts_no_package.json",
            [
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
            ],
        ),
    ),
)
async def test_bad_alerts(
    hass: HomeAssistant,
    hass_ws_client,
    aioclient_mock: AiohttpClientMocker,
    ha_version,
    fixture,
    expected_alerts,
) -> None:
    """Test creating issues based on alerts."""

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=load_fixture(fixture, "homeassistant_alerts"),
    )

    activated_components = (
        "darksky",
        "hikvision",
        "hikvisioncam",
    )
    for domain in activated_components:
        hass.config.components.add(domain)

    with patch(
        "homeassistant.components.homeassistant_alerts.alert.__version__",
        ha_version,
    ):
        assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "resolution_center/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "issues": [
            {
                "breaks_in_ha_version": None,
                "dismissed": False,
                "dismissed_version": None,
                "domain": "homeassistant_alerts",
                "is_fixable": False,
                "issue_id": f"{alert}_{integration}",
                "learn_more_url": f"https://alerts.home-assistant.io/#{alert}",
                "severity": "warning",
                "translation_key": "alert",
                "translation_placeholders": {"integration": integration},
            }
            for alert, integration in expected_alerts
        ]
    }


async def test_no_alerts(
    hass: HomeAssistant,
    hass_ws_client,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test creating issues based on alerts."""

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text="",
    )

    assert await async_setup_component(hass, DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "resolution_center/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"issues": []}


@pytest.mark.parametrize(
    "ha_version, fixture_1, expected_alerts_1, fixture_2, expected_alerts_2",
    (
        (
            "2022.7.0",
            "alerts_1.json",
            [
                ("aladdin_connect.markdown", "aladdin_connect"),
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("hive_us.markdown", "hive"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
            "alerts_2.json",
            [
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("hive_us.markdown", "hive"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
        ),
        (
            "2022.7.0",
            "alerts_2.json",
            [
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("hive_us.markdown", "hive"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
            "alerts_1.json",
            [
                ("aladdin_connect.markdown", "aladdin_connect"),
                ("dark_sky.markdown", "darksky"),
                ("hikvision.markdown", "hikvision"),
                ("hikvision.markdown", "hikvisioncam"),
                ("hive_us.markdown", "hive"),
                ("homematicip_cloud.markdown", "homematicip_cloud"),
                ("logi_circle.markdown", "logi_circle"),
                ("neato.markdown", "neato"),
                ("nest.markdown", "nest"),
                ("senseme.markdown", "senseme"),
                ("sochain.markdown", "sochain"),
            ],
        ),
    ),
)
async def test_alerts_change(
    hass: HomeAssistant,
    hass_ws_client,
    aioclient_mock: AiohttpClientMocker,
    ha_version: str,
    fixture_1: str,
    expected_alerts_1: list[tuple(str, str)],
    fixture_2: str,
    expected_alerts_2: list[tuple(str, str)],
) -> None:
    """Test creating issues based on alerts."""

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=load_fixture(fixture_1, "homeassistant_alerts"),
    )

    activated_components = (
        "aladdin_connect",
        "darksky",
        "hikvision",
        "hikvisioncam",
        "hive",
        "homematicip_cloud",
        "logi_circle",
        "neato",
        "nest",
        "senseme",
        "sochain",
    )
    for domain in activated_components:
        hass.config.components.add(domain)

    with patch(
        "homeassistant.components.homeassistant_alerts.alert.__version__",
        ha_version,
    ):
        assert await async_setup_component(hass, DOMAIN, {})

    now = dt_util.utcnow()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "resolution_center/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert_lists_same(
        msg["result"]["issues"],
        [
            {
                "breaks_in_ha_version": None,
                "dismissed": False,
                "dismissed_version": None,
                "domain": "homeassistant_alerts",
                "is_fixable": False,
                "issue_id": f"{alert}_{integration}",
                "learn_more_url": f"https://alerts.home-assistant.io/#{alert}",
                "severity": "warning",
                "translation_key": "alert",
                "translation_placeholders": {"integration": integration},
            }
            for alert, integration in expected_alerts_1
        ],
    )

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=load_fixture(fixture_2, "homeassistant_alerts"),
    )

    future = now + timedelta(minutes=60, seconds=1)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "resolution_center/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert_lists_same(
        msg["result"]["issues"],
        [
            {
                "breaks_in_ha_version": None,
                "dismissed": False,
                "dismissed_version": None,
                "domain": "homeassistant_alerts",
                "is_fixable": False,
                "issue_id": f"{alert}_{integration}",
                "learn_more_url": f"https://alerts.home-assistant.io/#{alert}",
                "severity": "warning",
                "translation_key": "alert",
                "translation_placeholders": {"integration": integration},
            }
            for alert, integration in expected_alerts_2
        ],
    )
