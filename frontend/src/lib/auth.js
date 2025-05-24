export function isAuthenticated() {
  const token = localStorage.getItem('token');
  if (!token) return false;

  try {
    // Basic JWT validation (check if expired)
    const payload = JSON.parse(atob(token.split('.')[1]));
    const isValid = payload.exp * 1000 > Date.now();

    if (!isValid) {
      // Token is expired, remove it
      localStorage.removeItem('token');
      return false;
    }

    return true;
  } catch {
    localStorage.removeItem('token'); // Remove invalid token
    return false;
  }
}

export function logout() {
  localStorage.removeItem('token');
  // Force redirect to login
  window.location.href = '/login';
}
