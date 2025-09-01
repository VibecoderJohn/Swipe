from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, Biometric, Transaction
import bcrypt
import requests
from config import Config

bp = Blueprint('api', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    try:
        user_id = User.create(email, phone, password)
        access_token = create_access_token(identity=str(user_id))
        return jsonify({"userId": str(user_id), "jwt": access_token}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('emailOrPhone')
    password = data.get('password')
    if not identifier or not password:
        return jsonify({"error": "Identifier and password required"}), 400
    user = User.find_by_email_or_phone(identifier)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["passwordHash"]):
        return jsonify({"error": "Invalid credentials"}), 401
    access_token = create_access_token(identity=str(user["_id"]))
    return jsonify({"userId": str(user["_id"]), "jwt": access_token}), 200

@bp.route('/kyc/verify', methods=['POST'])
@jwt_required()
def kyc_verify():
    user_id = get_jwt_identity()
    data = request.get_json()
    bvn = data.get('bvn')
    documents = data.get('documents', [])
    if not bvn or not documents:
        return jsonify({"error": "BVN and documents required"}), 400
    # Mono KYC (mock for MVP)
    headers = {"mono-sec-key": Config.MONO_SECRET_KEY}
    response = requests.post(
        "https://api.withmono.com/v1/kyc/bvn",
        json={"bvn": bvn},
        headers=headers
    )
    if response.status_code != 200:
        return jsonify({"error": "KYC verification failed"}), 400
    User.update_kyc(user_id, bvn, documents)
    return jsonify({"kycStatus": "verified"}), 200

@bp.route('/enroll-biometrics', methods=['POST'])
@jwt_required()
def enroll_biometrics():
    user_id = get_jwt_identity()
    data = request.get_json()
    biometric_type = data.get('type')
    template = data.get('template')
    if not biometric_type or not template:
        return jsonify({"error": "Type and template required"}), 400
    try:
        biometric_id = Biometric.enroll(user_id, biometric_type, template)
        return jsonify({"biometricId": str(biometric_id)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/biometrics', methods=['GET'])
@jwt_required()
def list_biometrics():
    user_id = get_jwt_identity()
    biometrics = Biometric.list_for_user(user_id)
    return jsonify({"biometrics": biometrics}), 200

@bp.route('/biometrics/<biometric_id>', methods=['DELETE'])
@jwt_required()
def delete_biometric(biometric_id):
    user_id = get_jwt_identity()
    if Biometric.delete(biometric_id, user_id):
        return jsonify({"success": True}), 200
    return jsonify({"error": "Biometric not found"}), 404

@bp.route('/accounts/link', methods=['POST'])
@jwt_required()
def link_account():
    user_id = get_jwt_identity()
    data = request.get_json()
    mono_code = data.get('monoCode')
    if not mono_code:
        return jsonify({"error": "Mono code required"}), 400
    # Mono account linking
    headers = {"mono-sec-key": Config.MONO_SECRET_KEY}
    response = requests.post(
        "https://api.withmono.com/account/auth",
        json={"code": mono_code},
        headers=headers
    )
    if response.status_code != 200:
        return jsonify({"error": "Account linking failed"}), 400
    account_data = {
        "monoAccountId": response.json().get("id"),
        "bankName": response.json().get("institution", {}).get("name", "Unknown"),
        "accountNumberLast4": response.json().get("account", {}).get("account_number", "xxxx")[-4:]
    }
    User.add_linked_account(user_id, account_data)
    return jsonify(account_data), 201

@bp.route('/accounts', methods=['GET'])
@jwt_required()
def list_accounts():
    user_id = get_jwt_identity()
    accounts = User.get_linked_accounts(user_id)
    return jsonify({"accounts": accounts}), 200

@bp.route('/transaction/initiate', methods=['POST'])
@jwt_required()
def initiate_transaction():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount')  # in kobo
    recipient = data.get('recipient')
    account_id = data.get('accountId')
    if not amount or not recipient or not account_id:
        return jsonify({"error": "Amount, recipient, and account ID required"}), 400
    try:
        transaction_id = Transaction.initiate(user_id, amount, recipient, account_id)
        return jsonify({"transactionId": str(transaction_id)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/transaction/authenticate/<transaction_id>', methods=['POST'])
@jwt_required()
def authenticate_transaction(transaction_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    biometric_types = data.get('biometricTypes', [])
    templates = data.get('templates', [])
    if len(biometric_types) != len(templates):
        return jsonify({"error": "Mismatched types and templates"}), 400
    try:
        Transaction.authenticate(transaction_id, user_id, biometric_types, templates)
        return jsonify({"authenticated": True}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

@bp.route('/transaction/execute/<transaction_id>', methods=['POST'])
@jwt_required()
def execute_transaction(transaction_id):
    user_id = get_jwt_identity()
    try:
        paystack_id = Transaction.execute(transaction_id, user_id)
        return jsonify({"status": "executed", "paystackTransactionId": paystack_id}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/transactions', methods=['GET'])
@jwt_required()
def list_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.list_for_user(user_id)
    return jsonify({"transactions": transactions}), 200
