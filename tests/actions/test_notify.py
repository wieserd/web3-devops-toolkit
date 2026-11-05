import pytest
from unittest.mock import patch, MagicMock
import urllib.error

from src.actions.notify import send_notification

def test_notify_no_webhook_url():
    params = {
        'title': 'Test Deployment',
        'status': 'success',
        'contract': 'MyContract',
        'network': 'localhost'
    }
    result = send_notification(params)
    assert result['status'] == 'success'
    assert result['notified'] is False
    assert 'No webhook configured' in result['reason']

@patch('urllib.request.urlopen')
def test_notify_discord_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 204
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    params = {
        'webhook_url': 'https://discord.com/api/webhooks/123/abc',
        'title': 'Deployment Completed',
        'contract': 'Token',
        'network': 'sepolia',
        'address': '0x1234567890123456789012345678901234567890'
    }
    result = send_notification(params)
    assert result['status'] == 'success'
    assert result['notified'] is True
    assert result['http_code'] == 204
    mock_urlopen.assert_called_once()

@patch('urllib.request.urlopen')
def test_notify_slack_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    params = {
        'webhook_url': 'https://hooks.slack.com/services/T00/B00/X00',
        'title': 'Deployment Completed',
        'contract': 'Token',
        'network': 'arbitrum-sepolia',
        'address': '0x1234567890123456789012345678901234567890'
    }
    result = send_notification(params)
    assert result['status'] == 'success'
    assert result['notified'] is True

@patch('urllib.request.urlopen')
def test_notify_network_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

    params = {
        'webhook_url': 'https://discord.com/api/webhooks/invalid',
        'title': 'Deployment Failed'
    }
    result = send_notification(params)
    assert result['status'] == 'failure'
    assert 'Connection refused' in result['error']

def test_notify_address_fallback_from_deployed_contracts():
    params = {
        'title': 'Fallback test',
        'contract': 'MyContract'
    }
    deployed_contracts = {'MyContract': '0x9999999999999999999999999999999999999999'}
    result = send_notification(params, deployed_contracts=deployed_contracts)
    assert result['status'] == 'success'
    assert result['notified'] is False
