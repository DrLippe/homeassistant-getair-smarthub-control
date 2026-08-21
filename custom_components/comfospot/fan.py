"""Fan platform for ComfoSpot."""
from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import percentage_to_stage, stage_to_percentage
from .const import (
    DOMAIN,
    MODE_PRESET_MASK,
    PRESET_MODES,
    PRESET_MODES_INV,
    PRESET_NIGHT,
)
from .coordinator import ComfoSpotCoordinator
from .entity import ComfoSpotZoneEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ComfoSpot fans."""
    coordinator: ComfoSpotCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ComfoSpotFan(coordinator, addr) for addr in coordinator.data["zones"]
    )


class ComfoSpotFan(ComfoSpotZoneEntity, FanEntity):
    """A ComfoSpot ventilation zone as a fan."""

    _attr_name = None  # use the device/zone name
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 100
    _attr_preset_modes = list(PRESET_MODES)

    def __init__(self, coordinator: ComfoSpotCoordinator, addr: int) -> None:
        super().__init__(coordinator, addr)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zone{addr}_fan"

    @property
    def _stage(self) -> float:
        speed = self._zone.get("speed")
        return float(speed) if speed is not None else 0.0

    @property
    def is_on(self) -> bool | None:
        speed = self._zone.get("speed")
        if speed is None:
            return None
        return speed > 0

    @property
    def percentage(self) -> int | None:
        speed = self._zone.get("speed")
        if speed is None:
            return None
        return stage_to_percentage(float(speed))

    @property
    def preset_mode(self) -> str | None:
        """Decode the vendor preset independently of airflow direction."""
        raw_mode = self._zone.get("mode")
        if raw_mode is None:
            return None
        return PRESET_MODES_INV.get(raw_mode & MODE_PRESET_MASK)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.coordinator.async_set_preset(self._addr, PRESET_NIGHT)
        else:
            speed = percentage_to_stage(percentage)
            await self.coordinator.async_set_stage(self._addr, speed)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Apply normal, night, boost, or automatic manufacturer operation."""
        await self.coordinator.async_set_preset(self._addr, preset_mode)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is not None:
            speed = percentage_to_stage(percentage)
        else:
            speed = self._stage or self.coordinator.api.last_active_stage(self._addr)
        await self.coordinator.async_set_stage(self._addr, speed)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_preset(self._addr, PRESET_NIGHT)
        await self.coordinator.async_request_refresh()
