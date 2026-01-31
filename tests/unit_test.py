import pytest
from unittest.mock import patch, MagicMock
from src.app import app
import requests_mock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Verify the healthz endpoint is alive."""
    rv = client.get('/healthz')
    assert rv.status_code == 200
    assert b'healthy' in rv.data

def test_diag_logic(client):
    """Verify the diagnostic tool parses response data correctly."""
    target_url = "https://example.com"
    with requests_mock.Mocker() as m:
        m.get(target_url, text="mock data", status_code=200)

        rv = client.get(f'/diag?url={target_url}')
        data = rv.get_json()

        assert rv.status_code == 200
        assert data['http_code'] == 200
        assert 'total_time_ms' in data
        assert 'speed_download_bps' in data

def test_status_memory_fallback(client):
    """Verify /status returns memory fallback when no Redis is configured."""
    rv = client.get('/status')
    data = rv.get_json()

    assert rv.status_code == 200
    assert data['backend'] == 'memory'
    assert data['connected'] is False
    assert 'message' in data

@patch('src.app.redis_url', 'redis://fake-host:6379')
@patch('src.app.redis')
def test_status_redis_connected(mock_redis, client):
    """Verify /status returns Redis info when connected."""
    mock_conn = MagicMock()
    mock_conn.info.side_effect = lambda section="default": {
        "server": {"redis_version": "7.2.0", "uptime_in_seconds": 86400},
        "clients": {"connected_clients": 3},
        "memory": {"used_memory_human": "1.5M"},
    }.get(section, {})
    mock_redis.from_url.return_value = mock_conn

    rv = client.get('/status')
    data = rv.get_json()

    assert rv.status_code == 200
    assert data['backend'] == 'redis'
    assert data['connected'] is True
    assert data['version'] == '7.2.0'
    assert data['uptime_seconds'] == 86400
    assert data['connected_clients'] == 3
    assert data['used_memory_human'] == '1.5M'
    assert 'latency_ms' in data

@patch('src.app.redis_url', 'redis://fake-host:6379')
@patch('src.app.redis')
def test_status_redis_connection_failure(mock_redis, client):
    """Verify /status returns 503 when Redis connection fails."""
    mock_redis.from_url.side_effect = ConnectionError("Connection refused")

    rv = client.get('/status')
    data = rv.get_json()

    assert rv.status_code == 503
    assert data['backend'] == 'redis'
    assert data['connected'] is False
    assert 'error' in data
