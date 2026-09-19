import api from './api'

// Spaces are addressed by slug everywhere except the listing.
// Paged endpoints take page (1-based) and optional pageSize, and resolve to
// { items, count }, where count is the total across all pages.
const spaceService = {
    async listSpaces() {
        const { data } = await api.get('/api/spaces/')
        return data
    },

    // Matches name or description, case-insensitively.
    async searchSpaces(query, { page = 1, pageSize } = {}) {
        const { data } = await api.get('/api/spaces/search', {
            params: { q: query, page, page_size: pageSize },
        })
        return data
    },

    async createSpace(payload) {
        const { data } = await api.post('/api/spaces/', payload)
        return data
    },

    async getSpace(slug) {
        const { data } = await api.get(`/api/spaces/${slug}`)
        return data
    },

    // Every field is optional; only what you pass is changed.
    async updateSpace(slug, payload) {
        const { data } = await api.patch(`/api/spaces/${slug}`, payload)
        return data
    },

    async deleteSpace(slug) {
        await api.delete(`/api/spaces/${slug}`)
    },

    // sort is 'new', 'old' or 'votes'.
    async listSpacePosts(slug, { sort = 'new', page = 1, pageSize } = {}) {
        const { data } = await api.get(`/api/spaces/${slug}/posts`, {
            params: { sort, page, page_size: pageSize },
        })
        return data
    },

    async createSpacePost(slug, payload) {
        const { data } = await api.post(`/api/spaces/${slug}/posts`, payload)
        return data
    },

    async listMembers(slug) {
        const { data } = await api.get(`/api/spaces/${slug}/members`)
        return data
    },

    async joinSpace(slug) {
        const { data } = await api.post(`/api/spaces/${slug}/join`)
        return data
    },

    async leaveSpace(slug) {
        await api.post(`/api/spaces/${slug}/leave`)
    },

    async addModerator(slug, username) {
        const { data } = await api.post(`/api/spaces/${slug}/moderators`, { username })
        return data
    },

    async removeModerator(slug, username) {
        await api.delete(`/api/spaces/${slug}/moderators/${username}`)
    },
}

export default spaceService
