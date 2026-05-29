import yaml

with open('prefect_grace/packet_registry.yaml', 'r') as f:
    data = yaml.safe_load(f) or {}

data['FEAT-UNKNOWN-W01-DYNAMIC-PLANNING'] = {
    'feature_id': 'FEAT-UNKNOWN',
    'packet_id': 'FEAT-UNKNOWN-W01-DYNAMIC-PLANNING',
    'path': 'prefect_grace/packets/FEAT-UNKNOWN/EXECUTION_PACKET.md',
    'reasoning': 'medium',
    'role': 'coder',
    'wave_id': 'W01'
}

with open('prefect_grace/packet_registry.yaml', 'w') as f:
    yaml.dump(data, f, sort_keys=False)
