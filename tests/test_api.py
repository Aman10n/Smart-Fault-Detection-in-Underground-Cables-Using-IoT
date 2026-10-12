import pytest

from app import CABLE_CONFIG, app, network


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    network.clear_fault()
    with app.test_client() as test_client:
        yield test_client
    network.clear_fault()


def test_dashboard_and_read_only_apis(client):
    dashboard = client.get('/')
    config = client.get('/api/config')
    data = client.get('/api/data')
    health = client.get('/api/health')

    assert dashboard.status_code == 200
    assert b'Smart Fault Detection' in dashboard.data
    assert config.get_json()['num_segments'] == CABLE_CONFIG['num_segments']
    assert len(data.get_json()['segments']) == CABLE_CONFIG['num_segments']
    assert health.get_json()['status'] == 'healthy'


def test_api_responses_include_security_and_cache_headers(client):
    response = client.get('/api/data')

    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize(
    ('payload', 'message'),
    [
        ({'segment_id': 'bad'}, 'Segment ID must be an integer'),
        ({'segment_id': 999}, 'Segment ID must be between'),
        ({'fault_type': 'unknown'}, 'Unknown fault type'),
    ],
)
def test_fault_api_rejects_invalid_payloads(client, payload, message):
    response = client.post('/api/faults', json=payload)

    assert response.status_code == 400
    assert message in response.get_json()['error']


def test_fault_api_supports_complete_lifecycle(client):
    created = client.post(
        '/api/faults',
        json={'segment_id': 4, 'fault_type': 'water_ingress'},
    )

    assert created.status_code == 201
    assert created.get_json()['segment_id'] == 4
    assert client.get('/api/health').get_json()['status'] == 'degraded'

    cleared = client.delete('/api/faults/4')
    assert cleared.status_code == 204
    assert client.get('/api/health').get_json()['status'] == 'healthy'


def test_diagnostic_endpoints_report_results_and_conflicts(client):
    no_fault = client.post('/api/diagnostics/murray')
    assert no_fault.status_code == 409

    client.post('/api/faults', json={'segment_id': 8, 'fault_type': 'short_circuit'})
    tdr = client.post('/api/diagnostics/tdr')
    murray = client.post('/api/diagnostics/murray')

    assert len(tdr.get_json()['waveform']) == 500
    assert murray.status_code == 200
    assert murray.get_json()['fault_type'] == 'Short Circuit'
