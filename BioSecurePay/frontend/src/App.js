import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import { register, login } from './api/api';
import './App.css';

const App = () => {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('jwt');
    if (token) {
      setUser({ token });
    }
  }, []);

  const handleRegister = async () => {
    try {
      const res = await register(email, phone, password);
      localStorage.setItem('jwt', res.data.jwt);
      setUser({ userId: res.data.userId });
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
    }
  };

  const handleLogin = async () => {
    try {
      const res = await login(email, password);
      localStorage.setItem('jwt', res.data.jwt);
      setUser({ userId: res.data.userId });
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    }
  };

  return (
    <Router>
      <div className="App">
        <h1>Welcome to BioSecurePay</h1>
        <p>Secure payments with biometric authentication</p>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <Switch>
          <Route exact path="/">
            <div>
              <h2>Register or Login</h2>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
              />
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Phone (+234...)"
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
              />
              <button onClick={handleRegister}>Register</button>
              <button onClick={handleLogin}>Login</button>
            </div>
          </Route>
          <Route path="/dashboard">
            <h2>Dashboard</h2>
            <p>User: {user ? user.userId : 'Not logged in'}</p>
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

export default App;
