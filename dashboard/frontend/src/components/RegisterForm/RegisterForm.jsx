import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './RegisterForm.css';

const RegisterForm = () => {
  const { role } = useParams();
  const navigate = useNavigate();
  const { register, loading, error } = useAuth();
  
  const [formData, setFormData] = useState({
    name: '', email: '', password: '', confirmPassword: '', phone: '',
    // Student fields
    studentId: '', university: '', year: '',
    // Counselor/Therapist fields
    licenseNumber: '', specialization: [], experience: '',
    // Admin/Institute fields
    instituteName: '', position: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'specialization') {
      setFormData({
        ...formData,
        [name]: value.split(',').map(item => item.trim()).filter(Boolean)
      });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    // Map possible route names to backend role names
    let backendRole = role;
    if (role === 'institute') backendRole = 'admin';
    if (role === 'therapist') backendRole = 'counselor';

    const userData = { 
      ...formData, 
      role: backendRole,
      experience: formData.experience ? Number(formData.experience) : undefined,
      year: formData.year ? Number(formData.year) : undefined
    };
    delete userData.confirmPassword;

    const result = await register(userData);
    if (result.success) {
      navigate(`/${backendRole}`);
    }
  };

  const renderRoleSpecificFields = () => {
    if (role === 'student') {
      return (
        <>
          <input
            type="text"
            name="studentId"
            placeholder="Student ID"
            value={formData.studentId}
            onChange={handleChange}
            required
          />
          <input
            type="text"
            name="university"
            placeholder="University"
            value={formData.university}
            onChange={handleChange}
            required
          />
          <input
            type="number"
            name="year"
            placeholder="Year of Study (1-5)"
            value={formData.year}
            onChange={handleChange}
            min="1"
            max="5"
            required
          />
        </>
      );
    }
    if (role === 'counselor' || role === 'therapist') {
      return (
        <>
          <input
            type="text"
            name="licenseNumber"
            placeholder="License Number"
            value={formData.licenseNumber}
            onChange={handleChange}
            required
          />
          <input
            type="text"
            name="specialization"
            placeholder="Specialization (e.g., Anxiety, Depression, PTSD)"
            value={formData.specialization.join(', ')}
            onChange={handleChange}
            required
          />
          <input
            type="number"
            name="experience"
            placeholder="Years of Experience"
            value={formData.experience}
            onChange={handleChange}
            min="0"
            required
          />
        </>
      );
    }
    if (role === 'admin' || role === 'institute') {
      return (
        <>
          <input
            type="text"
            name="instituteName"
            placeholder="Institute Name"
            value={formData.instituteName}
            onChange={handleChange}
            required
          />
          <input
            type="text"
            name="position"
            placeholder="Position (e.g., Director, Administrator)"
            value={formData.position}
            onChange={handleChange}
            required
          />
        </>
      );
    }
    return null;
  };

  return (
    <div className="register-form-container">
      <form className="register-form" onSubmit={handleSubmit}>
        <h2>Register as {role.charAt(0).toUpperCase() + role.slice(1)}</h2>
        {error && <div className="error">⚠️ {error}</div>}
        <input
          type="text"
          name="name"
          placeholder="Full Name"
          value={formData.name}
          onChange={handleChange}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="Email Address"
          value={formData.email}
          onChange={handleChange}
          required
        />
        <input
          type="tel"
          name="phone"
          placeholder="Phone Number"
          value={formData.phone}
          onChange={handleChange}
        />
        {renderRoleSpecificFields()}
        <input
          type="password"
          name="password"
          placeholder="Password (min 6 characters)"
          value={formData.password}
          onChange={handleChange}
          minLength="6"
          required
        />
        <input
          type="password"
          name="confirmPassword"
          placeholder="Confirm Password"
          value={formData.confirmPassword}
          onChange={handleChange}
          minLength="6"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Creating Account...' : 'Register'}
        </button>
        <div className="switch-auth">
          Already have an account?
          <span onClick={() => navigate('/login')}> Login here</span>
        </div>
      </form>
    </div>
  );
};

export default RegisterForm;