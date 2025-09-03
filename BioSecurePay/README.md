BioSecure Pay
BioSecure Pay is a secure mobile payment app using biometric authentication (fingerprint, face, voice) with Paystack for payments and Mono for KYC and account linking.
Features

User registration and login with JWT
KYC verification via Mono
Biometric enrollment and multi-factor authentication
Account linking with Mono
Secure transactions with Paystack
Analytics (Firebase) and monitoring (Sentry)
Deployed on Render

Setup

Clone: git clone https://github.com/yourusername/BioSecurePay.git
Backend:
cd backend
Install: pip install -r requirements.txt
Set .env (MONGO_URI, JWT_SECRET_KEY, PAYSTACK_SECRET_KEY, MONO_SECRET_KEY, SENTRY_DSN)
Run: flask run


Frontend:
cd frontend
Install: npm install
Set .env (API_URL, SENTRY_DSN)
Build: npx react-native run-android or npx react-native run-ios


MongoDB Atlas: Set up cluster, add connection string to backend/.env.

Deployment

Backend: Deploy to Render (Docker).
Frontend: Build APK/IPA, distribute via Google Play/TestFlight.
CI/CD: GitHub Actions (ci-cd.yml).

Testing

Backend: cd backend && pytest
Frontend: cd frontend && npm test

License
This project is licensed under the MIT License. See the LICENSE file for details.
Contributing
Submit pull requests to main. Ensure tests pass and follow NDPR/PCI-DSS guidelines.
Contact

X: @BioSecurePay
Email: support@biosecurepay.com
