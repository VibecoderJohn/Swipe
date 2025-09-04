from bson.objectid import ObjectId
from datetime import datetime
import bcrypt
from cryptography.fernet import Fernet
import requests
from .config import Config
from .extensions import mongo

ENCRYPTION_KEY = b'QGQ2OYEWEanrk8RNHBWsO0KPVSk3JNaNcw38Pjw5bJg='
cipher = Fernet(ENCRYPTION_KEY)

class User:
    @classmethod
    def create(cls, email, phone, password):
        collection = mongo.db.users
        if collection.find_one({"email": email}):
            raise ValueError("Email already exists")
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            "email": email,
            "phone": phone,
            "passwordHash": password_hash,
            "kycStatus": "pending",
            "kycDocuments": [],
            "linkedAccounts": [],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        return collection.insert_one(user_data).inserted_id

    @classmethod
    def find_by_email_or_phone(cls, identifier):
        collection = mongo.db.users
        return collection.find_one({"$or": [{"email": identifier}, {"phone": identifier}]})

    @classmethod
    def update_kyc(cls, user_id, bvn, documents, status="verified"):
        collection = mongo.db.users
        collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "bvn": bvn,
                "kycStatus": status,
                "kycDocuments": documents,
                "updatedAt": datetime.utcnow()
            }}
        )

    @classmethod
    def add_linked_account(cls, user_id, account_data):
        collection = mongo.db.users
        collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"linkedAccounts": account_data},
             "$set": {"updatedAt": datetime.utcnow()}}
        )

    @classmethod
    def get_linked_accounts(cls, user_id):
        collection = mongo.db.users
        user = collection.find_one({"_id": ObjectId(user_id)})
        return user.get("linkedAccounts", []) if user else []

class Biometric:
    @classmethod
    def enroll(cls, user_id, biometric_type, template):
        collection = mongo.db.biometrics
        if biometric_type not in ["fingerprint", "face", "voice"]:
            raise ValueError("Invalid biometric type")
        if collection.find_one({"userId": ObjectId(user_id), "type": biometric_type}):
            raise ValueError("Biometric type already enrolled")
        encrypted_template = cipher.encrypt(template.encode('utf-8')).decode('utf-8')
        biometric_data = {
            "userId": ObjectId(user_id),
            "type": biometric_type,
            "template": encrypted_template,
            "enrolledAt": datetime.utcnow(),
            "status": "active"
        }
        return collection.insert_one(biometric_data).inserted_id

    @classmethod
    def list_for_user(cls, user_id):
        collection = mongo.db.biometrics
        biometrics = collection.find({"userId": ObjectId(user_id)})
        return [{"id": str(b["_id"]), "type": b["type"], "enrolledAt": b["enrolledAt"], "status": b["status"]} for b in biometrics]

    @classmethod
    def delete(cls, biometric_id, user_id):
        collection = mongo.db.biometrics
        result = collection.delete_one({"_id": ObjectId(biometric_id), "userId": ObjectId(user_id)})
        return result.deleted_count > 0

    @classmethod
    def get_template(cls, user_id, biometric_type):
        collection = mongo.db.biometrics
        biometric = collection.find_one({"userId": ObjectId(user_id), "type": biometric_type})
        if biometric:
            return cipher.decrypt(biometric["template"].encode('utf-8')).decode('utf-8')
        return None

class Transaction:
    @classmethod
    def initiate(cls, user_id, amount, recipient, account_id):
        collection = mongo.db.transactions
        headers = {"Authorization": f"Bearer {Config.PAYSTACK_SECRET_KEY}"}
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json={"email": recipient, "amount": amount, "currency": "NGN"},
            headers=headers
        )
        if response.status_code != 200:
            raise ValueError("Paystack initialization failed")
        paystack_ref = response.json().get("data", {}).get("reference")

        transaction_data = {
            "userId": ObjectId(user_id),
            "type": "send",
            "amount": amount,
            "currency": "NGN",
            "recipient": recipient,
            "accountId": account_id,
            "status": "initiated",
            "biometricFactorsUsed": [],
            "paystackTransactionId": paystack_ref,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        return collection.insert_one(transaction_data).inserted_id

    @classmethod
    def authenticate(cls, transaction_id, user_id, biometric_types, templates):
        collection = mongo.db.transactions
        transaction = collection.find_one({"_id": ObjectId(transaction_id), "userId": ObjectId(user_id)})
        if not transaction or transaction["status"] != "initiated":
            raise ValueError("Invalid transaction")
        if len(biometric_types) < 2 and transaction["amount"] > 10000:
            raise ValueError("Multi-factor required for high-value transactions")
        for b_type, template in zip(biometric_types, templates):
            stored_template = Biometric.get_template(user_id, b_type)
            if not stored_template:
                raise ValueError(f"No enrolled {b_type} found")
            if stored_template != template:
                raise ValueError(f"{b_type} authentication failed - mismatch")
        collection.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {
                "status": "authenticated",
                "biometricFactorsUsed": biometric_types,
                "updatedAt": datetime.utcnow()
            }}
        )

    @classmethod
    def execute(cls, transaction_id, user_id):
        collection = mongo.db.transactions
        transaction = collection.find_one({"_id": ObjectId(transaction_id), "userId": ObjectId(user_id)})
        if not transaction or transaction["status"] != "authenticated":
            raise ValueError("Transaction not authenticated")
        headers = {"Authorization": f"Bearer {Config.PAYSTACK_SECRET_KEY}"}
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{transaction['paystackTransactionId']}",
            headers=headers
        )
        if response.status_code != 200 or response.json().get("data", {}).get("status") != "success":
            raise ValueError("Paystack verification failed")
        collection.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {
                "status": "executed",
                "updatedAt": datetime.utcnow()
            }}
        )
        return transaction['paystackTransactionId']

    @classmethod
    def list_for_user(cls, user_id):
        collection = mongo.db.transactions
        transactions = collection.find({"userId": ObjectId(user_id)})
        return [{"id": str(t["_id"]), "amount": t["amount"], "status": t["status"], "createdAt": t["createdAt"]} for t in transactions]
