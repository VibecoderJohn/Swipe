import React, { useContext } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthContext } from '../context/AuthContext';
import RegistrationScreen from '../screens/RegistrationScreen';
import KYCScreen from '../screens/KYCScreen';
import EnrollmentScreen from '../screens/EnrollmentScreen';
import DashboardScreen from '../screens/DashboardScreen';
import TransactionScreen from '../screens/TransactionScreen';

const Stack = createNativeStackNavigator();

const AppNavigator = () => {
  const { token, loading } = useContext(AuthContext);

  if (loading) return null;

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={token ? 'Dashboard' : 'Registration'}>
        <Stack.Screen name="Registration" component={RegistrationScreen} />
        <Stack.Screen name="KYC" component={KYCScreen} />
        <Stack.Screen name="Enrollment" component={EnrollmentScreen} />
        <Stack.Screen name="Dashboard" component={DashboardScreen} />
        <Stack.Screen name="Transaction" component={TransactionScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
