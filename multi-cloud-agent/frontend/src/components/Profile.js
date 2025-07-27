import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Profile = () => {
  const { user } = useAuth();

  return (
    <div className="profile-container">
      <h2>User Profile</h2>
      <p><strong>Name:</strong> {user.name || 'N/A'}</p>
      <p><strong>Email:</strong> {user.email}</p>
    </div>
  );
};

export default Profile;
