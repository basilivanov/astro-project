import pytest
from prefect_grace.platform.dag import (
    DAGValidationResult,
    validate_packet_dag,
    detect_cycles,
    topological_sort,
    compute_ready_packets,
)


def test_validate_empty_dag():
    result = validate_packet_dag([])
    assert result.packets_total == 0
    assert result.ordered_packets == []
    assert result.cycles == []
    assert result.ready_packets == []


def test_validate_single_packet_no_deps():
    packets = [
        {"packet_id": "P1", "depends_on": []},
    ]
    result = validate_packet_dag(packets)
    assert result.packets_total == 1
    assert result.ordered_packets == ["P1"]
    assert result.ready_packets == ["P1"]
    assert result.cycles == []


def test_validate_linear_dependency():
    packets = [
        {"packet_id": "P1", "depends_on": []},
        {"packet_id": "P2", "depends_on": ["P1"]},
        {"packet_id": "P3", "depends_on": ["P2"]},
    ]
    result = validate_packet_dag(packets)
    assert result.packets_total == 3
    assert result.ordered_packets == ["P1", "P2", "P3"]
    assert result.ready_packets == ["P1"]
    assert result.cycles == []


def test_validate_missing_dependency():
    packets = [
        {"packet_id": "P1", "depends_on": ["P_MISSING"]},
    ]
    result = validate_packet_dag(packets)
    assert result.packets_total == 1
    assert "P1" in result.missing_dependencies
    assert "P_MISSING" in result.missing_dependencies["P1"]
    assert "P1" in result.cascading_blocked


def test_detect_simple_cycle():
    packets = [
        {"packet_id": "P1", "depends_on": ["P2"]},
        {"packet_id": "P2", "depends_on": ["P1"]},
    ]
    result = validate_packet_dag(packets)
    assert result.packets_total == 2
    assert len(result.cycles) > 0
    assert len(result.cascading_blocked) == 2


def test_detect_three_node_cycle():
    packets = [
        {"packet_id": "P1", "depends_on": ["P2"]},
        {"packet_id": "P2", "depends_on": ["P3"]},
        {"packet_id": "P3", "depends_on": ["P1"]},
    ]
    result = validate_packet_dag(packets)
    assert result.packets_total == 3
    assert len(result.cycles) > 0
    assert len(result.cascading_blocked) == 3


def test_multiple_roots():
    packets = [
        {"packet_id": "P1", "depends_on": []},
        {"packet_id": "P2", "depends_on": []},
        {"packet_id": "P3", "depends_on": ["P1", "P2"]},
    ]
    result = validate_packet_dag(packets)
    assert result.packets_total == 3
    assert set(result.ready_packets) == {"P1", "P2"}
    assert result.cycles == []


def test_compute_ready_packets_with_blocked():
    packets = [
        {"packet_id": "P1", "depends_on": []},
        {"packet_id": "P2", "depends_on": []},
        {"packet_id": "P3", "depends_on": ["P1"]},
    ]
    blocked = {"P2"}
    ready = compute_ready_packets(packets, blocked)
    assert "P1" in ready
    assert "P2" not in ready
    assert "P3" not in ready


def test_topological_sort_simple():
    graph = {
        "P1": [],
        "P2": ["P1"],
        "P3": ["P2"],
    }
    all_nodes = {"P1", "P2", "P3"}
    result = topological_sort(graph, all_nodes)
    assert result == ["P1", "P2", "P3"]


def test_topological_sort_with_cycle():
    graph = {
        "P1": ["P2"],
        "P2": ["P1"],
    }
    all_nodes = {"P1", "P2"}
    result = topological_sort(graph, all_nodes)
    assert result == []


def test_detect_cycles_no_cycle():
    graph = {
        "P1": [],
        "P2": ["P1"],
    }
    cycles = detect_cycles(graph)
    assert cycles == []


def test_detect_cycles_self_loop():
    graph = {
        "P1": ["P1"],
    }
    cycles = detect_cycles(graph)
    assert len(cycles) > 0
