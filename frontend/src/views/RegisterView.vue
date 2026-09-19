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
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const submitting = ref(false)
const detail = ref('')
const fields = ref({})

async function onSubmit() {
  detail.value = ''
  fields.value = {}

  if (password.value !== confirmPassword.value) {
    fields.value = { confirmPassword: ['The passwords do not match.'] }
    return
  }

  submitting.value = true

  try {
    // Registering signs the new account in, so go straight on.
    const user = await userService.register({
      username: username.value,
      email: email.value,
      password: password.value,
    })
    userStore.setUser(user)
    await router.push(route.query.redirect ?? { name: 'home' })
  } catch (error) {
    const parsed = parseApiError(error, 'Could not create your account.')
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
      <CardTitle class="text-xl">Sign up</CardTitle>
      <CardDescription>Create your saiddit account.</CardDescription>
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
        <Label for="email">Email</Label>
        <Input
          id="email"
          v-model="email"
          type="email"
          autocomplete="email"
          required
          :aria-invalid="Boolean(firstError(fields, 'email'))"
        />
        <p v-if="firstError(fields, 'email')" class="text-sm text-destructive">
          {{ firstError(fields, 'email') }}
        </p>
      </div>

      <div class="grid gap-2">
        <Label for="password">Password</Label>
        <Input
          id="password"
          v-model="password"
          type="password"
          autocomplete="new-password"
          required
          :aria-invalid="Boolean(firstError(fields, 'password'))"
        />
        <p v-if="firstError(fields, 'password')" class="text-sm text-destructive">
          {{ firstError(fields, 'password') }}
        </p>
      </div>

      <div class="grid gap-2">
        <Label for="confirm-password">Confirm password</Label>
        <Input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          required
          :aria-invalid="Boolean(firstError(fields, 'confirmPassword'))"
        />
        <p v-if="firstError(fields, 'confirmPassword')" class="text-sm text-destructive">
          {{ firstError(fields, 'confirmPassword') }}
        </p>
      </div>
    </CardContent>

    <CardFooter class="mt-6 flex-col gap-4">
      <Button type="submit" class="w-full" :disabled="submitting">
        {{ submitting ? 'Creating account…' : 'Sign up' }}
      </Button>

      <p class="text-sm text-muted-foreground">
        Already have an account?
        <RouterLink :to="{ name: 'login', query: route.query }" class="text-primary underline-offset-4 hover:underline">
          Log in
        </RouterLink>
      </p>
    </CardFooter>
  </form>
</template>
