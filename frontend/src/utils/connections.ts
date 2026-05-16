const ACTIVE_CONNECTION_KEY = 'active_connection_ref'

export function getActiveConnectionRef() {
  return localStorage.getItem(ACTIVE_CONNECTION_KEY)
}

export function setActiveConnectionRef(connectionRef: string) {
  localStorage.setItem(ACTIVE_CONNECTION_KEY, connectionRef)
}

