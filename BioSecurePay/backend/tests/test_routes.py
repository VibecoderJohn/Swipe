import pytest
from app import create_app
from flask_jwt_extended import create_access_token
from bson import ObjectId
import json

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mongo(app):
    return app.mongo

@pytest.fixture
def user_id(client, mongo):
    response = client.post('/api/v1/register', json={
        'email': 'test@example.com',
        'phone': '+2348012345678',
        'password': 'password123'
    })
    user_id = json.loads(response.data)['userId']
    return user_id

@pytest.fixture
def token(user_id):
    return create_access_token(identity=user_id)

def test_register_success(client, mongo):
    mongo.db.users.drop()
    response = client.post('/api/v1/register', json={
        'email': 'newuser@example.com',
        'phone': '+2348098765432',
        'password': 'securepass'
    })
    assert response.status_code == 201
    assert 'userId' in response.json
    assert 'jwt' in response.json

def test_register_duplicate_email(client, mongo):
    response = client.post('/api/v1/register', json={
        'email': 'test@example.com',
        'phone': '+2348012345678',
        'password': 'password123'
    })
    assert response.status_code == 400
    assert response.json['error'] == 'Email already exists'

def test_login_success(client, user_id):
    response = client.post('/api/v1/login', json={
        'emailOrPhone': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'jwt' in response.json

def test_login_invalid_credentials(client):
    response = client.post('/api/v1/login', json={
        'emailOrPhone': 'wrong@example.com',
        'password': 'wrong'
    })
    assert response.status_code == 401
    assert 'error' in response.json

def test_kyc_verify_success(client, user_id, token, monkeypatch):
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"status": "success"}
        return MockResponse()
    monkeypatch.setattr(requests, 'post', mock_post)
    
    response = client.post('/api/v1/kyc/verify', json={
        'bvn': '12345678901',
        'documents': ['s3://doc.jpg', 's3://selfie.jpg']
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['kycStatus'] == 'verified'

def test_enroll_biometrics_success(client, user_id, token):
    response = client.post('/api/v1/enroll-biometrics', json={
        'type': 'fingerprint',
        'template': 'mock_fingerprint_template'
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 201
    assert 'biometricId' in response.json

def test_enroll_biometrics_duplicate(client, user_id, token):
    client.post('/api/v1/enroll-biometrics', json={
        'type': 'fingerprint',
        'template': 'mock_fingerprint_template'
    }, headers={'Authorization': f'Bearer {token}'})
    response = client.post('/api/v1/enroll-biometrics', json={
        'type': 'fingerprint',
        'template': 'mock_fingerprint_template'
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    assert response.json['error'] == 'Biometric type already enrolled'

def test_transaction_initiate_success(client, user_id, token, monkeypatch):
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": {"reference": "mock_ref_123"}}
        return MockResponse()
    monkeypatch.setattr(requests, 'post', mock_post)
    
    response = client.post('/api/v1/transaction/initiate', json={
        'amount': 5000,
        'recipient': 'recipient@example.com',
        'accountId': 'mock_acc_123'
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 201
    assert 'transactionId' in response.json

def test_transaction_authenticate_success(client, user_id, token, mongo, monkeypatch):
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": {"reference": "mock_ref_123"}}
        return MockResponse()
    monkeypatch.setattr(requests, 'post', mock_post)
    
    client.post('/api/v1/enroll-biometrics', json={
        'type': 'fingerprint',
        'template': 'mock_fingerprint_template'
    }, headers={'Authorization': f'Bearer {token}'})
    client.post('/api/v1/enroll-biometrics', json={
        'type': 'voice',
        'template': 'mock_voice_template'
    }, headers={'Authorization': f'Bearer {token}'})
    
    response = client.post('/api/v1/transaction/initiate', json={
        'amount': 5000,
        'recipient': 'recipient@example.com',
        'accountId': 'mock_acc_123'
    }, headers={'Authorization': f'Bearer {token}'})
    txn_id = response.json['transactionId']
    
    response = client.post(f'/api/v1/transaction/authenticate/{txn_id}', json={
        'biometricTypes': ['fingerprint', 'voice'],
        'templates': ['mock_fingerprint_template', 'mock_voice_template']
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['authenticated'] is True

def test_transaction_authenticate_invalid_template(client, user_id, token, monkeypatch):
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": {"reference": "mock_ref_123"}}
        return MockResponse()
    monkeypatch.setattr(requests, 'post', mock_post)
    
    response = client.post('/api/v1/transaction/initiate', json={
        'amount': 5000,
        'recipient': 'recipient@example.com',
        'accountId': 'mock_acc_123'
    }, headers={'Authorization': f'Bearer {token}'})
    txn_id = response.json['transactionId']
    
    response = client.post(f'/api/v1/transaction/authenticate/{txn_id}', json={
        'biometricTypes': ['fingerprint'],
        'templates': ['wrong_template']
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 401
    assert 'fingerprint authentication failed - mismatch' in response.json['error']

def test_security_no_jwt(client):
    response = client.post('/api/v1/kyc/verify', json={
        'bvn': '12345678901',
        'documents': ['s3://doc.jpg', 's3://selfie.jpg']
    })
    assert response.status_code == 401
    assert 'Missing Authorization Header' in response.json['message']

def test_security_invalid_input(client, user_id, token):
    response = client.post('/api/v1/kyc/verify', json={
        'bvn': '<script>alert(1)</script>',
        'documents': []
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    assert 'BVN and documents required' in response.json['error']
