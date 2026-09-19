<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// Resolve who (if anyone) is signed in before the rest of the app asks.
onMounted(() => userStore.fetchCurrentUser())
</script>

<template>
  <RouterView />
</template>
