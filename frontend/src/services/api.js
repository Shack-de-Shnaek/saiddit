import axios from 'axios'
import { router } from '@/router'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
    withCredentials: true,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
    withXSRFToken: true,
})

const CSRF_URL = '/api/auth/csrf'

// Requests that are allowed to fail with a 401 without kicking the visitor to
// the login page: the auth endpoints themselves, plus anything that opts out
// with `{ skipAuthRedirect: true }`.
const PUBLIC_AUTH_URLS = ['/api/auth/login', '/api/auth/register', CSRF_URL]

// Django checks CSRF on every method that isn't safe, not just POST.
const UNSAFE_METHODS = ['post', 'put', 'patch', 'delete']

api.interceptors.request.use(async (config) => {
    if (UNSAFE_METHODS.includes(config.method) && config.url !== CSRF_URL) {
        await api.post(CSRF_URL)
    }
    return config
})

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const config = error.config ?? {}
        const unauthenticated = error.response?.status === 401

        if (unauthenticated && !config.skipAuthRedirect && !PUBLIC_AUTH_URLS.includes(config.url)) {
            const current = router.currentRoute.value

            if (current.name !== 'login') {
                router.push({
                    name: 'login',
                    // Come back to where the session expired once signed in again.
                    query: { redirect: current.fullPath },
                })
            }
        }

        return Promise.reject(error)
    },
)

export default api
