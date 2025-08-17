const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://multi-cloud-ai-management-agent.onrender.com';

export async function login({ email, password }) {
  const response = await fetch(`${API_BASE_URL}/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      username: email,
      password: password,
    }).toString(),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Login failed');
  }

  const data = await response.json();
  // Assuming the backend returns access_token and token_type
  localStorage.setItem('access_token', data.access_token);
  return data;
}

export async function signup({ email, password, name }) {
  const response = await fetch(`${API_BASE_URL}/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password, name }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Signup failed');
  }

  const data = await response.json();
  return data;
}