import axios from 'axios'
import type { AxiosError } from 'axios'

import type { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse } from '../types/auth'
import type { CreateConnectionRequest, DatabaseConnection } from '../types/connection'
import type { HistoryItem } from '../types/history'
import type { ApprovalRequest, ApprovalResponse, QueryRequest, QueryResponse } from '../types/query'
import { getAuthToken, logout } from '../utils/auth'

import type { SchemaResponse } from '../types/schema'

const API_BASE_URL = 'https://ai-db-copilot.onrender.com'

console.log('API URL:', API_BASE_URL)

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      logout()

      if (!window.location.pathname.includes('/login')) {
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  },
)

export const queryApi = {
  generateSql: async (payload: QueryRequest) => {
    const { data } = await apiClient.post<QueryResponse>('/query', payload)
    return data
  },
  approveQuery: async (payload: ApprovalRequest) => {
    const { data } = await apiClient.post<ApprovalResponse>('/approve', payload)
    return data
  },
}

export const authApi = {
  login: async (payload: LoginRequest) => {
    const { data } = await apiClient.post<LoginResponse>('/login', payload)
    return data
  },
  register: async (payload: RegisterRequest) => {
    const { data } = await apiClient.post<RegisterResponse>('/register', payload)
    return data
  },
}

export const connectionApi = {
  listConnections: async () => {
    const { data } = await apiClient.get<DatabaseConnection[]>('/connections')
    return data
  },
  createConnection: async (payload: CreateConnectionRequest) => {
    const { data } = await apiClient.post('/connections', payload)
    return data
  },
}

export const historyApi = {
  listHistory: async () => {
    const { data } = await apiClient.get<HistoryItem[]>('/history')
    return data
  },
}

export const schemaApi = {
  getSchema: async (connectionRef: string) => {
    const { data } = await apiClient.get<SchemaResponse>(
      `/schema?connection_ref=${encodeURIComponent(connectionRef)}`,
    )

    return data
  },
}

type ApiErrorResponse = {
  detail?: string
  message?: string
}

export function getApiErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<ApiErrorResponse>

  if (axiosError.code === 'ERR_NETWORK') {
    return 'Unable to reach the API. Confirm the backend is running and try again.'
  }

  return axiosError.response?.data?.detail || axiosError.response?.data?.message || fallback
}
