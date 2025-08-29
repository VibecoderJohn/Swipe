from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash
from bson import ObjectId
import requests
import base64
import os
from datetime import datetime
from paystackapi.paystack import Paystack  # Correct import for Paystack

app = Flask(__name__)
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
mongo = PyMongo(app)
jwt = JWTManager(app)

# Paystack Configuration
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
paystack = Paystack(secret_key=PAYSTACK_SECRET_KEY)  # Instantiate Paystack

# Mono Configuration
MONO_SECRET_KEY = os.environ.get('MONO_SECRET_KEY')
MONO_API_BASE = 'https://api.withmono.com'

# Default Route
@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'BioSecure Pay API is running', 'status': 'online'}), 200

# Register User
@app.route('/api/v1/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    full_name = data.get('full_name')
    password = data.get('password')

    if not all([email, full_name, password]):
        return jsonify({'error': 'Missing required fields', 'code': 400}), 400

    if mongo.db.users.find_one({'email': email}):
        return jsonify({'error': 'Email already exists', 'code': 409}), 409

    user_id = mongo.db.users.insert_one({
        'email': email,
        'phone': phone,
        'full_name': full_name,
        'password': generate_password_hash(password),
        'kyc_status': 'pending',
        'linked_accounts': [],
        'created_at': datetime.utcnow(),
    }).inserted_id

    token = create_access_token(identity=str(user_id))
    return jsonify({'user_id': str(user_id), 'token': token}), 201

# KYC Verification
@app.route('/api/v1/kyc/verify', methods=['POST'])
@jwt_required()
def kyc_verify():
    data = request.get_json()
    documents = data.get('documents', [])
    user_id = request.jwt_identity
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'kyc_status': 'pending', 'kyc_documents': documents}}
    )
    return jsonify({'status': 'pending'}), 200

# Enroll Biometrics
@app.route('/api/v1/enroll-biometrics', methods=['POST'])
@jwt_required()
def enroll_biometrics():
    data = request.get_json()
    biometric_type = data.get('type')
    template_data = data.get('template_data')

    if biometric_type not in ['fingerprint', 'face', 'voice']:
        return jsonify({'error': 'Invalid biometric type', 'code': 400}), 400

    # Simulate biometric template encryption
    encrypted_template = base64.b64encode(template_data.encode()).decode()

    biometric_id = mongo.db.biometrics.insert_one({
        'user_id': ObjectId(request.jwt_identity),
        'type': biometric_type,
        'template': encrypted_template,
        'enrolled_at': datetime.utcnow(),
        'status': 'active',
    }).inserted_id

    return jsonify({'success': True, 'biometric_id': str(biometric_id)}), 201

# Verify Biometrics
@app.route('/api/v1/verify-biometrics', methods=['POST'])
@jwt_required()
def verify_biometrics():
    data = request.get_json()
    biometric_type = data.get('type')
    input_data = data.get('input_data')

    biometric = mongo.db.biometrics.find_one({
        'user_id': ObjectId(request.jwt_identity),
        'type': biometric_type,
        'status': 'active',
    })

    if not biometric:
        return jsonify({'error': 'Biometric not found', 'code': 404}), 404

    # Simplified verification
    is_valid = base64.b64encode(input_data.encode()).decode() == biometric['template']
    return jsonify({'verified': is_valid}), 200

# Link Bank Account (Mono)
@app.route('/api/v1/link-account', methods=['POST'])
@jwt_required()
def link_account():
    data = request.get_json()
    mono_code = data.get('mono_code')
    try:
        response = requests.post(
            f'{MONO_API_BASE}/account/auth',
            headers={'mono-sec-key': MONO_SECRET_KEY},
            json={'code': mono_code}
        )
        response.raise_for_status()
        account_data = response.json()
        account_info = [{
            'mono_account_id': account_data['account']['id'],
            'bank_name': account_data['account']['institution']['name'],
            'account_type': account_data['account']['type']
        }]
        
        mongo.db.users.update_one(
            {'_id': ObjectId(request.jwt_identity)},
            {'$push': {'linked_accounts': {'$each': account_info}}}
        )
        return jsonify({'linked_account_id': account_info[0]['mono_account_id']}), 200
    except requests.RequestException as e:
        return jsonify({'error': str(e), 'code': 400}), 400

# Initiate Transaction
@app.route('/api/v1/transaction/initiate', methods=['POST'])
@jwt_required()
def initiate_transaction():
    data = request.get_json()
    amount = data.get('amount')
    recipient = data.get('recipient')
    mono_account_id = data.get('mono_account_id')

    user = mongo.db.users.find_one({'_id': ObjectId(request.jwt_identity)})
    if not any(acc.get('mono_account_id') == mono_account_id for acc in user.get('linked_accounts', [])):
        return jsonify({'error': 'Invalid account', 'code': 400}), 400

    transaction_id = mongo.db.transactions.insert_one({
        'user_id': ObjectId(request.jwt_identity),
        'amount': amount,
        'recipient': recipient,
        'status': 'initiated',
        'mono_account_id': mono_account_id,
        'created_at': datetime.utcnow(),
        'logs': [{'event': 'initiated', 'timestamp': datetime.utcnow()}],
    }).inserted_id

    return jsonify({'transaction_id': str(transaction_id)}), 201

# Authenticate Transaction
@app.route('/api/v1/transaction/authenticate', methods=['POST'])
@jwt_required()
def authenticate_transaction():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    biometric_types = data.get('biometric_types')
    input_data = data.get('input_data')

    transaction = mongo.db.transactions.find_one({'_id': ObjectId(transaction_id)})
    if not transaction or transaction['user_id'] != ObjectId(request.jwt_identity):
        return jsonify({'error': 'Invalid transaction', 'code': 400}), 400

    for b_type in biometric_types:
        biometric = mongo.db.biometrics.find_one({'user_id': transaction['user_id'], 'type': b_type})
        if not biometric or base64.b64encode(input_data.encode()).decode() != biometric['template']:
            return jsonify({'error': 'Biometric verification failed', 'code': 401}), 401

    mongo.db.transactions.update_one(
        {'_id': ObjectId(transaction_id)},
        {'$set': {'status': 'authenticated', 'biometric_auth': biometric_types, 'logs': [{'event': 'authenticated', 'timestamp': datetime.utcnow()}]}}
    )
    return jsonify({'authenticated': True}), 200

# Execute Transaction (Paystack)
@app.route('/api/v1/transaction/execute', methods=['POST'])
@jwt_required()
def execute_transaction():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    transaction = mongo.db.transactions.find_one({'_id': ObjectId(transaction_id)})
    if not transaction or transaction['status'] != 'authenticated':
        return jsonify({'error': 'Transaction not authenticated', 'code': 400}), 400

    try:
        response = paystack.transaction.initialize(
            amount=int(transaction['amount'] * 100),  # Convert to kobo
            email=transaction['recipient'],
            reference=str(transaction['_id'])
        )
        if response['status']:
            mongo.db.transactions.update_one(
                {'_id': ObjectId(transaction_id)},
                {'$set': {
                    'status': 'executed',
                    'paystack_reference': response['data']['reference'],
                    'executed_at': datetime.utcnow(),
                    'logs': [{'event': 'executed', 'timestamp': datetime.utcnow()}]
                }}
            )
            return jsonify({'status': 'executed', 'paystack_reference': response['data']['reference']}), 200
        else:
            return jsonify({'error': response['message'], 'code': 400}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'code': 400}), 400
