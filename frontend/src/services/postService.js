import api from './api'

// Posts are created through spaceService; a post is always read by id here.
// Comment listings are paged: they take page (1-based) and optional pageSize,
// and resolve to { items, count }. Each comment carries reply_count; its
// replies are fetched with listReplies.
const postService = {
    async getPost(postId) {
        const { data } = await api.get(`/api/posts/${postId}`)
        return data
    },

    async deletePost(postId) {
        await api.delete(`/api/posts/${postId}`)
    },

    async listComments(postId, { page = 1, pageSize } = {}) {
        const { data } = await api.get(`/api/posts/${postId}/comments`, {
            params: { page, page_size: pageSize },
        })
        return data
    },

    async listReplies(commentId, { page = 1, pageSize } = {}) {
        const { data } = await api.get(`/api/posts/comments/${commentId}/replies`, {
            params: { page, page_size: pageSize },
        })
        return data
    },

    // Attaches image files to a post; multipart, one 'images' part per file.
    async addImages(postId, files) {
        const form = new FormData()
        for (const file of files) form.append('images', file)

        const { data } = await api.post(`/api/posts/${postId}/images`, form)
        return data
    },

    async addComment(postId, content) {
        const { data } = await api.post(`/api/posts/${postId}/comments`, { content })
        return data
    },

    async replyToComment(commentId, content) {
        const { data } = await api.post(`/api/posts/comments/${commentId}/replies`, { content })
        return data
    },

    async deleteComment(commentId) {
        await api.delete(`/api/posts/comments/${commentId}`)
    },

    // voteType is 1 for an upvote, -1 for a downvote.
    async voteOnPost(postId, voteType) {
        const { data } = await api.post(`/api/posts/${postId}/vote`, { vote_type: voteType })
        return data
    },

    async unvotePost(postId) {
        await api.delete(`/api/posts/${postId}/vote`)
    },

    async voteOnComment(commentId, voteType) {
        const { data } = await api.post(`/api/posts/comments/${commentId}/vote`, { vote_type: voteType })
        return data
    },

    async unvoteComment(commentId) {
        await api.delete(`/api/posts/comments/${commentId}/vote`)
    },
}

export default postService
