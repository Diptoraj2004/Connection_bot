import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './LoginForm.css';

const LoginForm = () => {
  const { login, error, loading, user } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const navigate = useNavigate();

  const handleChange = e => setForm({...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    const result = await login(form.email, form.password);
    if(result.success && user?.role) navigate(`/${user.role}`);
  };

  return (
    <div className="login-form-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Login</h2>
        {error && <div className="error">{error}</div>}
        <input name="email" value={form.email} onChange={handleChange} type="email" placeholder="Email" required />
        <input name="password" value={form.password} onChange={handleChange} type="password" placeholder="Password" required />
        <button type="submit" disabled={loading}>{loading ? "Logging in..." : "Login"}</button>
        <div className="switch-auth">
          No account? <span onClick={()=>navigate('/')}>Create one</span>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;