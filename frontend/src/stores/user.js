import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import userService from '@/services/userService'

// The signed-in user. `user` is null for a guest, so a null value after
// `loaded` turns true is what tells us nobody is logged in.
export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  // Spaces the user is a member of; always empty for a guest.
  const spaces = ref([])
  const loading = ref(false)
  const loaded = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const fullName = computed(() => {
    if (!user.value) return ''
    return [user.value.first_name, user.value.last_name].filter(Boolean).join(' ')
  })
  // What to show in the UI: a real name when the account has one, else the handle.
  const displayName = computed(() => fullName.value || user.value?.username || '')

  function setUser(value) {
    user.value = value ?? null
    loaded.value = true

    if (user.value === null) spaces.value = []
  }

  // Safe to call for a guest: it just leaves the list empty.
  async function fetchMemberSpaces() {
    if (user.value === null) {
      spaces.value = []
      return
    }

    spaces.value = await userService.mySpaces()
  }

  // Called once on app mount. currentUser() answers null for a guest instead
  // of throwing, and opts out of the 401 redirect.
  async function fetchCurrentUser() {
    loading.value = true

    try {
      setUser(await userService.currentUser())

      // Only a signed-in visitor has memberships to fetch.
      if (user.value !== null) await fetchMemberSpaces()
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await userService.logout()
    } finally {
      // Whatever the server said, this browser is done with the session.
      setUser(null)
    }
  }

  return {
    user,
    spaces,
    loading,
    loaded,
    isAuthenticated,
    fullName,
    displayName,
    setUser,
    fetchMemberSpaces,
    fetchCurrentUser,
    logout,
  }
})
