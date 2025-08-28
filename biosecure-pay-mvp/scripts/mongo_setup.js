// MongoDB setup script to initialize database and create indexes
const { MongoClient } = require('mongodb');

async function setupDatabase() {
  const uri = 'mongodb://localhost:27017';
  const client = new MongoClient(uri);

  try {
    await client.connect();
    const db = client.db('biosecurepay');

    // Create Users Collection
    await db.createCollection('users');
    await db.collection('users').createIndex({ email: 1 }, { unique: true });
    await db.collection('users').createIndex({ kyc_status: 1 });

    // Create Biometrics Collection
    await db.createCollection('biometrics');
    await db.collection('biometrics').createIndex(
      { user_id: 1, type: 1 },
      { unique: true }
    );

    // Create Transactions Collection
    await db.createCollection('transactions');
    await db.collection('transactions').createIndex({ user_id: 1 });
    await db.collection('transactions').createIndex({ status: 1 });

    console.log('Database and indexes created successfully');
  } catch (error) {
    console.error('Error setting up database:', error);
  } finally {
    await client.close();
  }
}

setupDatabase();
