import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import RegistrationScreen from '../../src/screens/RegistrationScreen';
import { AuthContext } from '../../src/context/AuthContext';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const mockNavigate = jest.fn();
const mockRegister = jest.fn();

const Stack = createNativeStackNavigator();

const renderWithContext = (component) => {
  return render(
    <AuthContext.Provider value={{ register: mockRegister }}>
      <NavigationContainer>
        <Stack.Navigator>
          <Stack.Screen name="Registration" component={component} />
        </Stack.Navigator>
      </NavigationContainer>
    </AuthContext.Provider>
  );
};

describe('RegistrationScreen', () => {
  it('renders correctly', () => {
    const { getByPlaceholderText, getByText } = renderWithContext(RegistrationScreen);
    expect(getByPlaceholderText('Email')).toBeTruthy();
    expect(getByPlaceholderText('Phone')).toBeTruthy();
    expect(getByPlaceholderText('Password')).toBeTruthy();
    expect(getByText('Register')).toBeTruthy();
  });

  it('handles successful registration', async () => {
    mockRegister.mockResolvedValue(true);
    const { getByPlaceholderText, getByText } = renderWithContext(RegistrationScreen);
    
    fireEvent.changeText(getByPlaceholderText('Email'), 'test@example.com');
    fireEvent.changeText(getByPlaceholderText('Phone'), '+2348012345678');
    fireEvent.changeText(getByPlaceholderText('Password'), 'password123');
    fireEvent.press(getByText('Register'));
    
    expect(mockRegister).toHaveBeenCalledWith('test@example.com', '+2348012345678', 'password123');
  });

  it('handles failed registration', async () => {
    mockRegister.mockResolvedValue(false);
    jest.spyOn(require('react-native'), 'Alert').mockImplementation(({ alert }) => alert());
    const { getByPlaceholderText, getByText } = renderWithContext(RegistrationScreen);
    
    fireEvent.changeText(getByPlaceholderText('Email'), 'test@example.com');
    fireEvent.changeText(getByPlaceholderText('Phone'), '+2348012345678');
    fireEvent.changeText(getByPlaceholderText('Password'), 'password123');
    fireEvent.press(getByText('Register'));
    
    expect(mockRegister).toHaveBeenCalled();
    expect(require('react-native').Alert.alert).toHaveBeenCalledWith('Error', 'Registration failed');
  });

  it('shows error for missing fields', () => {
    jest.spyOn(require('react-native'), 'Alert').mockImplementation(({ alert }) => alert());
    const { getByText } = renderWithContext(RegistrationScreen);
    
    fireEvent.press(getByText('Register'));
    expect(require('react-native').Alert.alert).toHaveBeenCalledWith('Error', 'All fields required');
  });
});
