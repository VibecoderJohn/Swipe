# BioSecure Pay MVP

Monorepo for BioSecure Pay fintech app.

## Structure
- backend/: Flask API
- frontend/: React Native app
- scripts/: Utilities

## Local Setup
### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. Copy .env.example to .env and fill values
4. `python app.py`

### Frontend
1. `cd frontend`
2. `yarn install`
3. For iOS: `cd ios && pod install`
4. Copy .env.example to .env and fill values
5. `yarn start`

### Database
Run `node ../scripts/mongo_setup.js` to init MongoDB (update URI in script).

## Deployment
- Backend on Render: Use render.yaml
- Database: MongoDB Atlas
- Frontend: Build APK/IPA and distribute.

License: MIT
