<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import userService from '@/services/userService'
import { useUserStore } from '@/stores/user'
import { parseApiError, firstError } from '@/lib/apiError'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const detail = ref('')
const fields = ref({})

async function onSubmit() {
  submitting.value = true
  detail.value = ''
  fields.value = {}

  try {
    // The login response is the user, so the store needs no second call.
    userStore.setUser(await userService.login(username.value, password.value))
    await userStore.fetchMemberSpaces()
    await router.push(route.query.redirect ?? { name: 'home' })
  } catch (error) {
    const parsed = parseApiError(error, 'Could not sign you in.')
    detail.value = parsed.detail
    fields.value = parsed.fields
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <CardHeader>
      <CardTitle class="text-xl">Log in</CardTitle>
      <CardDescription>Welcome back to saiddit.</CardDescription>
    </CardHeader>

    <CardContent class="flex flex-col gap-4 pt-6">
      <Alert v-if="detail" variant="destructive">
        <AlertDescription>{{ detail }}</AlertDescription>
      </Alert>

      <div class="grid gap-2">
        <Label for="username">Username</Label>
        <Input
          id="username"
          v-model="username"
          autocomplete="username"
          required
          :aria-invalid="Boolean(firstError(fields, 'username'))"
        />
        <p v-if="firstError(fields, 'username')" class="text-sm text-destructive">
          {{ firstError(fields, 'username') }}
        </p>
      </div>

      <div class="grid gap-2">
        <Label for="password">Password</Label>
        <Input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          :aria-invalid="Boolean(firstError(fields, 'password'))"
        />
        <p v-if="firstError(fields, 'password')" class="text-sm text-destructive">
          {{ firstError(fields, 'password') }}
        </p>
      </div>
    </CardContent>

    <CardFooter class="mt-6 flex-col gap-4">
      <Button type="submit" class="w-full" :disabled="submitting">
        {{ submitting ? 'Logging in…' : 'Log in' }}
      </Button>

      <p class="text-sm text-muted-foreground">
        New here?
        <RouterLink :to="{ name: 'register', query: route.query }" class="text-primary underline-offset-4 hover:underline">
          Create an account
        </RouterLink>
      </p>
    </CardFooter>
  </form>
</template>
