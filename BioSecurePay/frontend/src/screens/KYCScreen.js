import React, { useState } from 'react';
import { View, TextInput, Button, Alert, StyleSheet } from 'react-native';
import ImagePicker from 'react-native-image-picker';
import api from '../api/api';
import { logKYC } from '../utils/Analytics';

const KYCScreen = ({ navigation }) => {
  const [bvn, setBvn] = useState('');
  const [documentUri, setDocumentUri] = useState(null);
  const [selfieUri, setSelfieUri] = useState(null);

  const pickImage = (type) => {
    const options = { noData: true };
    ImagePicker.launchCamera(options, (response) => {
      if (response.uri) {
        if (type === 'document') setDocumentUri(response.uri);
        else setSelfieUri(response.uri);
      } else if (response.errorCode) {
        Alert.alert('Error', response.errorMessage);
      }
    });
  };

  const submitKYC = async () => {
    if (!bvn || !documentUri || !selfieUri) {
      Alert.alert('Error', 'All fields required');
      return;
    }
    try {
      await api.post('/kyc/verify', { bvn, documents: [documentUri, selfieUri] });
      logKYC();
      Alert.alert('Success', 'KYC submitted');
      navigation.navigate('Enrollment');
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'KYC submission failed');
    }
  };

  return (
    <View style={styles.container}>
      <TextInput style={styles.input} placeholder="BVN" value={bvn} onChangeText={setBvn} keyboardType="numeric" />
      <Button title="Upload ID Document" onPress={() => pickImage('document')} />
      <Button title="Take Selfie" onPress={() => pickImage('selfie')} />
      <Button title="Submit KYC" onPress={submitKYC} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: 'center' },
  input: { borderWidth: 1, marginBottom: 10, padding: 10 },
});

export default KYCScreen;
