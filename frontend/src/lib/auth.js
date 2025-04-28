export function isAuthenticated() {
  // Example: check for token in localStorage
  return !!localStorage.getItem('token');
}
