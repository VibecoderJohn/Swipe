import React, { useState } from 'react';
import { View, Button, Alert, Text, StyleSheet } from 'react-native';
import Biometrics from 'react-native-biometrics';
import Voice from '@react-native-voice/voice';
import { enrollBiometric } from '../api/api';
import { logBiometricEnrolled } from '../utils/Analytics';

const EnrollmentScreen = ({ navigation }) => {
  const [status, setStatus] = useState('');

  const enroll = async (type) => {
    setStatus(`Enrolling ${type}...`);
    try {
      let template = '';
      if (type === 'fingerprint' || type === 'face') {
        const rnBiometrics = new Biometrics();
        const { available } = await rnBiometrics.isSensorAvailable();
        if (!available) throw new Error(`${type} not available`);
        const { success } = await rnBiometrics.simplePrompt({ promptMessage: `Enroll ${type}` });
        if (success) template = `mock_${type}_template_${Date.now()}`;
      } else if (type === 'voice') {
        await Voice.start('en-US');
        return new Promise((resolve) => {
          Voice.onSpeechResults = (e) => {
            template = e.value[0];
            Voice.stop();
            resolve();
          };
        });
      }
      if (template) {
        await enrollBiometric(type, template);
        logBiometricEnrolled(type);
        Alert.alert('Success', `${type} enrolled`);
      }
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error || 'Enrollment failed');
    } finally {
      setStatus('');
    }
  };

  return (
    <View style={styles.container}>
      <Text>{status}</Text>
      <Button title="Enroll Fingerprint" onPress={() => enroll('fingerprint')} />
      <Button title="Enroll Face" onPress={() => enroll('face')} />
      <Button title="Enroll Voice" onPress={() => enroll('voice')} />
      <Button title="Finish Enrollment" onPress={() => navigation.navigate('Dashboard')} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: 'center' },
});

export default EnrollmentScreen;
