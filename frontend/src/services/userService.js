import api from './api'

// Session auth. Only the auth endpoints live here for now.
const userService = {
    async register(payload) {
        const { data } = await api.post('/api/auth/register', payload)
        return data
    },

    async login(username, password) {
        const { data } = await api.post('/api/auth/login', { username, password })
        return data
    },

    async logout() {
        await api.post('/api/auth/logout')
    },

    async me(config) {
        const { data } = await api.get('/api/auth/me', config)
        return data
    },

    // The spaces the signed-in user is a member of.
    async mySpaces() {
        const { data } = await api.get('/api/spaces/my-spaces')
        return data
    },

    // Same as me(), but a signed-out visitor is null instead of a 401 throw.
    async currentUser() {
        try {
            // A 401 here is the expected answer for a guest, not a session
            // that expired, so don't let the interceptor bounce to /login.
            return await this.me({ skipAuthRedirect: true })
        } catch (error) {
            if (error.response?.status === 401) return null
            throw error
        }
    },
}

export default userService
