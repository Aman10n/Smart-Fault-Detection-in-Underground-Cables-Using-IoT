import pytest

from app import app, network, socketio


@pytest.fixture()
def socket_client():
    app.config.update(TESTING=True)
    network.clear_fault()
    flask_client = app.test_client()
    client = socketio.test_client(app, flask_test_client=flask_client)
    yield client
    if client.is_connected():
        client.disconnect()
    network.clear_fault()


def received_events(client):
    return {packet['name']: packet.get('args', []) for packet in client.get_received()}


def test_connect_sends_configuration_and_initial_telemetry(socket_client):
    events = received_events(socket_client)

    assert socket_client.is_connected()
    assert events['connected'][0]['status'] == 'ok'
    assert len(events['sensor_data'][0]['segments']) == 20


def test_invalid_fault_payload_returns_operation_error(socket_client):
    socket_client.get_received()

    socket_client.emit('inject_fault', {'segment_id': 'invalid', 'fault_type': 'short_circuit'})
    events = received_events(socket_client)

    assert 'operation_error' in events
    assert 'integer' in events['operation_error'][0]['message']


def test_fault_injection_and_clear_events(socket_client):
    socket_client.get_received()

    socket_client.emit('inject_fault', {'segment_id': 6, 'fault_type': 'thermal_fault'})
    injected = received_events(socket_client)
    assert injected['fault_alert'][0]['segment_id'] == 6
    assert 'sensor_data' in injected

    socket_client.emit('clear_all_faults', {})
    cleared = received_events(socket_client)
    assert 'all_faults_cleared' in cleared
    assert network.get_overview()['active_fault_count'] == 0


def test_murray_event_requires_an_active_fault(socket_client):
    socket_client.get_received()

    socket_client.emit('run_murray', {})
    events = received_events(socket_client)

    assert events['murray_result'][0]['error'] == 'No active fault to locate'
