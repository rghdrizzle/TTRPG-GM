export function setToken(token: string) {
  localStorage.setItem("token", token)
}

export function getToken(): string | null {
  return localStorage.getItem("token")
}

export function logout() {
  localStorage.removeItem("token")
  window.location.href = "/login"
}

export function requireAuth(): string | null {
  const token = localStorage.getItem("token")
  if (!token) {
    window.location.href = "/login"
  }
  return token
}