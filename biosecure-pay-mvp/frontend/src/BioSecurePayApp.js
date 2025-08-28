import React, { useState } from 'react';
import { View, Text, TextInput, Button, Alert, ActivityIndicator } from 'react-native';
import { NativeBiometrics } from 'react-native-biometrics';
import Voice from '@react-native-voice/voice';
import axios from 'axios';
import { Paystack } from 'react-native-paystack-webview';
import { MonoConnect } from '@mono.co/react-native';

const API_BASE_URL = process.env.API_BASE_URL || 'https://your-render-app.onrender.com/api/v1';
const PAYSTACK_PUBLIC_KEY = process.env.PAYSTACK_PUBLIC_KEY || 'pk_test_your_paystack_key';
const MONO_PUBLIC_KEY = process.env.MONO_PUBLIC_KEY || 'test_pk_your_mono_key';

const BioSecurePayApp = () => {
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [fullName, setFullName] = useState('');
  const [kycDocs, setKycDocs] = useState([]);
  const [biometricType, setBiometricType] = useState('');
  const [monoCode, setMonoCode] = useState('');
  const [transactionData, setTransactionData] = useState({ amount: '', recipient: '' });
  const [loading, setLoading] = useState(false);
  const [transactionRef, setTransactionRef] = useState('');

  // Register User
  const handleRegister = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/register`, {
        email,
        phone,
        full_name: fullName,
        password: 'tempPassword123',
      });
      Alert.alert('Success', `User registered: ${response.data.user_id}`);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'Registration failed');
    }
    setLoading(false);
  };

  // KYC Verification
  const handleKycVerify = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/kyc/verify`, { documents: kycDocs });
      Alert.alert('Success', `KYC Status: ${response.data.status}`);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'KYC submission failed');
    }
    setLoading(false);
  };

  // Biometric Enrollment
  const handleEnrollBiometrics = async () => {
    setLoading(true);
    try {
      let templateData;
      if (biometricType === 'fingerprint' || biometricType === 'face') {
        const result = await NativeBiometrics.createSignature({
          promptMessage: 'Enroll Biometric',
        });
        templateData = result.signature;
      } else if (biometricType === 'voice') {
        await Voice.start('en-US');
        Voice.onSpeechResults = (e) => {
          templateData = e.value[0];
          Voice.stop();
        };
      }
      const response = await axios.post(`${API_BASE_URL}/enroll-biometrics`, {
        type: biometricType,
        template_data: templateData,
      });
      Alert.alert('Success', `Biometric enrolled: ${response.data.biometric_id}`);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'Biometric enrollment failed');
    }
    setLoading(false);
  };

  // Link Bank Account via Mono
  const handleMonoLink = async (code) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/link-account`, {
        mono_code: code,
      });
      setMonoCode(code);
      Alert.alert('Success', `Account linked: ${response.data.linked_account_id}`);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'Account linking failed');
    }
    setLoading(false);
  };

  // Initiate and Authenticate Transaction
  const handleTransaction = async () => {
    setLoading(true);
    try {
      // Initiate
      const initResponse = await axios.post(`${API_BASE_URL}/transaction/initiate`, {
        amount: parseFloat(transactionData.amount),
        recipient: transactionData.recipient,
        mono_account_id: monoCode,
      });
      const transactionId = initResponse.data.transaction_id;

      // Authenticate with Biometrics
      const biometricResult = await NativeBiometrics.createSignature({
        promptMessage: 'Authenticate Transaction',
      });
      const authResponse = await axios.post(`${API_BASE_URL}/transaction/authenticate`, {
        transaction_id: transactionId,
        biometric_types: ['face'],
        input_data: biometricResult.signature,
      });

      if (authResponse.data.authenticated) {
        setTransactionRef(transactionId); // Trigger Paystack payment
      }
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'Transaction failed');
    }
    setLoading(false);
  };

  return (
    <View style={{ padding: 20 }}>
      <Text>BioSecure Pay</Text>
      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        style={{ borderWidth: 1, marginBottom: 10 }}
      />
      <TextInput
        placeholder="Phone"
        value={phone}
        onChangeText={setPhone}
        style={{ borderWidth: 1, marginBottom: 10 }}
      />
      <TextInput
        placeholder="Full Name"
        value={fullName}
        onChangeText={setFullName}
        style={{ borderWidth: 1, marginBottom: 10 }}
      />
      <Button title="Register" onPress={handleRegister} disabled={loading} />
      <Button title="Submit KYC" onPress={handleKycVerify} disabled={loading} />
      <TextInput
        placeholder="Biometric Type (fingerprint/face/voice)"
        value={biometricType}
        onChangeText={setBiometricType}
        style={{ borderWidth: 1, marginBottom: 10 }}
      />
      <Button title="Enroll Biometrics" onPress={handleEnrollBiometrics} disabled={loading} />
      <MonoConnect
        publicKey={MONO_PUBLIC_KEY}
        onSuccess={(response) => handleMonoLink(response.code)}
        onClose={() => Alert.alert('Mono Exit')}
      >
        <Button title="Link Bank Account" disabled={loading} />
      </MonoConnect>
      <TextInput
        placeholder="Amount (NGN)"
        value={transactionData.amount}
        onChangeText={(text) => setTransactionData({ ...transactionData, amount: text })}
        style={{ borderWidth: 1, marginBottom: 10 }}
      />
      <TextInput
        placeholder="Recipient Email"
        value={transactionData.recipient}
        onChangeText={(text) => setTransactionData({ ...transactionData, recipient: text })}
        style={{ borderWidth: 1, marginBottom: 10 }}
      />
      <Button title="Initiate Transaction" onPress={handleTransaction} disabled={loading} />
      {transactionRef && (
        <Paystack
          paystackKey={PAYSTACK_PUBLIC_KEY}
          amount={parseFloat(transactionData.amount) * 100} // Convert to kobo
          email={transactionData.recipient}
          reference={transactionRef}
          onCancel={() => setTransactionRef('')}
          onSuccess={async (response) => {
            try {
              const executeResponse = await axios.post(`${API_BASE_URL}/transaction/execute`, {
                transaction_id: transactionRef,
              });
              Alert.alert('Success', `Transaction executed: ${executeResponse.data.paystack_reference}`);
              setTransactionRef('');
            } catch (error) {
              Alert.alert('Error', error.response?.data?.error || 'Transaction execution failed');
            }
          }}
        />
      )}
      {loading && <ActivityIndicator size="large" />}
    </View>
  );
};

export default BioSecurePayApp;
