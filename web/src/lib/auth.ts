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
    window.location.href = "/unauthorized"
    return null
  }

  try {
    const base64Url = token.split(".")[1]
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/")
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    )
    const payload = JSON.parse(jsonPayload)

    if (!payload.exp || Date.now() >= payload.exp * 1000) {
      localStorage.removeItem("token")
      console.log("Unauthorized: login again")
      window.location.href = "/unauthorized"
      return null
    }

    return token
  } catch {
    localStorage.removeItem("token")
    window.location.href = "/unauthorized"
    return null
  }
}

export function getUserId(): string | null {
  const token = localStorage.getItem("token")
  if (!token) {
    window.location.href = "/unauthorized"
    return null
  }
  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.user_id ?? payload.sub ?? null
  } catch {
    window.location.href = "/unauthorized"
    return null
  }
}

export function getUsername(): string | null {
  const token = localStorage.getItem("token")
  if (!token) {
    window.location.href = "/unauthorized"
    return null
  }
  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.username ?? null
  } catch {
    window.location.href = "/unauthorized"
    return null
  }
}