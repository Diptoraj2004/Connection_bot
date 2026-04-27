import React, { useState } from 'react';
import './RoleSelection.css';

// Import images
import studentImage from '../../assets/images/student.jpg';
import therapistImage from '../../assets/images/counselor.jpg';
import instituteImage from '../../assets/images/institute.jpg';

const RoleSelection = () => {
  const [selectedRole, setSelectedRole] = useState(null);

  const roles = [
    {
      id: 'student',
      title: 'STUDENT',
      description: 'Access wellness tracking, AI support, peer connections, and counseling resources',
      image: studentImage,
      features: ['Personal wellness dashboard', 'AI emotional support', 'Peer community', 'Academic stress management']
    },
    {
      id: 'therapist',
      title: 'THERAPIST',
      description: 'Manage patients, track progress, access clinical tools, and evidence-based resources',
      image: therapistImage,
      features: ['Patient management', 'Clinical decision support', 'Progress tracking', 'Secure documentation']
    },
    {
      id: 'institute',
      title: 'INSTITUTE',
      description: 'Monitor campus wellness, manage resources, track outcomes, and generate insights',
      image: instituteImage,
      features: ['Campus analytics', 'Resource allocation', 'Compliance monitoring', 'Population health insights']
    }
  ];

  const handleRoleSelect = (roleId) => {
    setSelectedRole(roleId);
    // Navigate to registration form for selected role
    setTimeout(() => {
      window.location.href = `/register/${roleId}`;
    }, 500);
  };

  return (
    <div className="role-selection-page">
      <header className="welcome-section">
        <div className="logo">
          <span className="logo-icon">🧠</span>
          <span className="logo-text">MindCare</span>
        </div>
        <h1>Want to create an account?</h1>
        <h2>Tell me for which profession?</h2>
        <p className="subtitle">Choose your role to get a personalized experience</p>
      </header>

      <main className="role-cards-container">
        {roles.map((role) => (
          <div 
            key={role.id}
            className={`role-card ${role.id}-card ${selectedRole === role.id ? 'selected' : ''}`}
            onClick={() => handleRoleSelect(role.id)}
          >
            <div className="card-image-container">
              <img 
                src={role.image} 
                alt={`${role.title} illustration`}
                className="card-image"
              />
            </div>
            <div className="card-content">
              <h3>{role.title}</h3>
              <p className="card-description">{role.description}</p>
              <ul className="feature-list">
                {role.features.map((feature, index) => (
                  <li key={index}>✓ {feature}</li>
                ))}
              </ul>
              <button className="select-role-btn">
                Choose {role.title.toLowerCase()}
              </button>
            </div>
            {selectedRole === role.id && (
              <div className="selection-checkmark">✓</div>
            )}
          </div>
        ))}
      </main>

      <footer className="page-footer">
        <p>Already have an account? <a href="/login">Sign in here</a></p>
        <div className="footer-links">
          <a href="/privacy">Privacy Policy</a>
          <a href="/terms">Terms of Service</a>
          <a href="/help">Help</a>
        </div>
      </footer>
    </div>
  );
};

export default RoleSelection;