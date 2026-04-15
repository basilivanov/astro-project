from prefect_grace.tasks.wave_executor import group_packets_by_wave, order_packets_for_wave, reviewer_target_packet_id


def test_group_packets_by_wave_sorts_waves() -> None:
    packets = [
        {"packet_id": "P3", "wave_id": "W02", "role": "coder", "dependencies": []},
        {"packet_id": "P1", "wave_id": "W01", "role": "coder", "dependencies": []},
        {"packet_id": "P2", "wave_id": "W10", "role": "coder", "dependencies": []},
    ]
    grouped = group_packets_by_wave(packets)
    assert [wave_id for wave_id, _ in grouped] == ["W01", "W02", "W10"]


def test_order_packets_for_wave_uses_dependencies_and_role_order() -> None:
    packets = [
        {"packet_id": "ARCH", "wave_id": "W01", "role": "architect", "dependencies": ["REV"]},
        {"packet_id": "REV", "wave_id": "W01", "role": "reviewer", "dependencies": ["CODER", "VER"]},
        {"packet_id": "VER", "wave_id": "W01", "role": "verifier", "dependencies": ["CODER"]},
        {"packet_id": "CODER", "wave_id": "W01", "role": "coder", "dependencies": []},
    ]
    ordered = order_packets_for_wave(packets)
    assert [packet["packet_id"] for packet in ordered] == ["CODER", "VER", "REV", "ARCH"]


def test_reviewer_target_packet_id_prefers_coder_dependency() -> None:
    packets = {
        "CODER": {"packet_id": "CODER", "role": "coder"},
        "VER": {"packet_id": "VER", "role": "verifier"},
        "REV": {"packet_id": "REV", "role": "reviewer", "dependencies": ["VER", "CODER"]},
    }
    assert reviewer_target_packet_id(packets["REV"], packets) == "CODER"
