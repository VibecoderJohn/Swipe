import requests
import pytest
from bson import ObjectId

@pytest.fixture
def base_url():
    return 'http://localhost:5000/api/v1'

@pytest.fixture
def client(base_url):
    return requests.Session()

def test_end_to_end_flow(base_url, client, monkeypatch):
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "paystack" in args[0]:
                    return {"data": {"reference": "mock_ref_123"}}
                return {"id": "mock_acc_123", "institution": {"name": "Mock Bank"}, "account": {"account_number": "1234567890"}}
        return MockResponse()
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": {"status": "success"}}
        return MockResponse()
    monkeypatch.setattr(requests, 'post', mock_post)
    monkeypatch.setattr(requests, 'get', mock_get)
    
    response = client.post(f'{base_url}/register', json={
        'email': 'integration@test.com',
        'phone': '+2348012345678',
        'password': 'password123'
    })
    assert response.status_code == 201
    token = response.json()['jwt']
    headers = {'Authorization': f'Bearer {token}'}

    response = client.post(f'{base_url}/kyc/verify', json={
        'bvn': '12345678901',
        'documents': ['s3://doc.jpg', 's3://selfie.jpg']
    }, headers=headers)
    assert response.status_code == 200

    response = client.post(f'{base_url}/enroll-biometrics', json={
        'type': 'fingerprint',
        'template': 'mock_fingerprint_template'
    }, headers=headers)
    assert response.status_code == 201
    response = client.post(f'{base_url}/enroll-biometrics', json={
        'type': 'voice',
        'template': 'mock_voice_template'
    }, headers=headers)
    assert response.status_code == 201

    response = client.post(f'{base_url}/accounts/link', json={
        'monoCode': 'mock_code'
    }, headers=headers)
    assert response.status_code == 201

    response = client.post(f'{base_url}/transaction/initiate', json={
        'amount': 5000,
        'recipient': 'recipient@example.com',
        'accountId': 'mock_acc_123'
    }, headers=headers)
    assert response.status_code == 201
    txn_id = response.json()['transactionId']

    response = client.post(f'{base_url}/transaction/authenticate/{txn_id}', json={
        'biometricTypes': ['fingerprint', 'voice'],
        'templates': ['mock_fingerprint_template', 'mock_voice_template']
    }, headers=headers)
    assert response.status_code == 200

    response = client.post(f'{base_url}/transaction/execute/{txn_id}', json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()['status'] == 'executed'

def test_network_failure(base_url, client, monkeypatch):
    def mock_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Network failure")
    monkeypatch.setattr(requests, 'post', mock_post)
    
    response = None
    try:
        response = client.post(f'{base_url}/register', json={
            'email': 'test@example.com',
            'phone': '+2348012345678',
            'password': 'password123'
        })
    except requests.exceptions.ConnectionError:
        pass
    assert response is None
