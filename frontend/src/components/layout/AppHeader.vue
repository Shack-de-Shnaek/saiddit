<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Button } from '@/components/ui/button'
import SpaceSearch from '@/components/layout/SpaceSearch.vue'
import ThemeToggle from '@/components/layout/ThemeToggle.vue'

const router = useRouter()
const userStore = useUserStore()

async function onLogout() {
  await userStore.logout()
  await router.push({ name: 'home' })
}
</script>

<template>
  <header class="sticky top-0 z-10 flex h-14 items-center gap-4 border-b bg-background px-4">
    <RouterLink to="/" class="text-lg font-bold">saiddit</RouterLink>

    <SpaceSearch />

    <ThemeToggle />

    <!-- Nothing until the current user resolves, so the button can't flip. -->
    <template v-if="userStore.loaded">
      <div v-if="userStore.isAuthenticated" class="flex items-center gap-3">
        <span class="text-sm text-muted-foreground">{{ userStore.displayName }}</span>
        <Button variant="outline" size="sm" class="rounded-full" @click="onLogout">
          Log out
        </Button>
      </div>

      <Button v-else as-child size="sm" class="rounded-full">
        <RouterLink :to="{ name: 'login' }">Log in</RouterLink>
      </Button>
    </template>
  </header>
</template>
