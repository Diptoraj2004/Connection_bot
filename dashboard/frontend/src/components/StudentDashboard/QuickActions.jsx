import React from 'react';
import { useNavigate } from 'react-router-dom';
import './QuickActions.css';

const QuickActions = () => {
  const navigate = useNavigate();

  const quickActionItems = [
    {
      id: 'book-session',
      title: 'Book Therapy Session',
      description: 'Schedule a session with a counselor',
      icon: '🗓️',
      action: () => navigate('/book-therapy'),
      primary: true
    },
    {
      id: 'mood-check',
      title: 'Mood Check-in',
      description: 'Log your current mood',
      icon: '😊',
      action: () => console.log('Mood check-in'),
      primary: false
    },
    {
      id: 'crisis-support',
      title: 'Crisis Support',
      description: 'Get immediate help',
      icon: '🆘',
      action: () => console.log('Crisis support'),
      primary: false,
      urgent: true
    }
  ];

  return (
    <div className="quick-actions">
      <h2 className="section-title">Quick Actions</h2>
      <div className="actions-grid">
        {quickActionItems.map(item => (
          <button
            type="button"
            key={item.id}
            className={`action-card ${item.primary ? 'primary' : ''} ${item.urgent ? 'urgent' : ''}`}
            onClick={item.action}
          >
            <div className="action-icon">{item.icon}</div>
            <div className="action-content">
              <h3 className="action-title">{item.title}</h3>
              <p className="action-description">{item.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;