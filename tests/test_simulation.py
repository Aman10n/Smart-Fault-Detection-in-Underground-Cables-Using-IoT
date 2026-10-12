import random

import pytest

from app import CABLE_CONFIG, FAULT_TYPES, CableNetwork, CableSegment, MurrayLoopTest, TDRSimulator


@pytest.fixture(autouse=True)
def deterministic_randomness():
    random.seed(42)


def test_normal_sensor_update_stays_within_physical_bounds():
    segment = CableSegment(0, 0.0, 0.5)

    segment.update_normal()

    assert segment.current >= 0
    assert 0 <= segment.humidity <= 100
    assert segment.partial_discharge >= 0
    assert 0 <= segment.health <= 100


@pytest.mark.parametrize("fault_type", FAULT_TYPES)
def test_every_fault_type_changes_segment_state(fault_type):
    segment = CableSegment(3, 1.5, 2.0)

    segment.apply_fault(fault_type)
    segment.update_with_fault()

    assert segment.fault_active is True
    assert segment.fault_type == fault_type
    assert segment.health < 60


def test_tdr_waveform_has_expected_shape_and_distance_range():
    waveform = TDRSimulator.generate_waveform(10.0, 4.25, "short_circuit", num_points=120)

    assert len(waveform) == 120
    assert waveform[0]["distance"] == 0
    assert waveform[-1]["distance"] <= 12
    assert {"time", "amplitude", "distance"} == waveform[0].keys()


def test_murray_loop_result_is_bounded_to_cable_length():
    result = MurrayLoopTest.calculate(10.0, 6.25, CABLE_CONFIG["resistance_per_km"])

    assert 0 <= result["measured_distance"] <= 10
    assert 0 <= result["accuracy"] <= 100
    assert result["error_meters"] >= 0


def test_network_fault_lifecycle_updates_overview():
    cable = CableNetwork()

    fault = cable.inject_fault(2, "ground_fault")
    assert fault["segment_id"] == 2
    assert cable.get_overview()["active_fault_count"] == 1

    cable.clear_fault(2)
    assert cable.get_overview()["active_fault_count"] == 0
    assert cable.segments[2].fault_active is False


def test_network_rejects_invalid_or_duplicate_faults():
    cable = CableNetwork()

    assert cable.inject_fault(-1, "ground_fault") is None
    assert cable.inject_fault(0, "not-a-fault") is None
    assert cable.inject_fault(0, "ground_fault") is not None
    assert cable.inject_fault(0, "thermal_fault") is None
