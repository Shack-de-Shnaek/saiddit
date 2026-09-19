<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import spaceService from '@/services/spaceService'
import { useUserStore } from '@/stores/user'
import { parseApiError, firstError } from '@/lib/apiError'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

const router = useRouter()
const userStore = useUserStore()

const name = ref('')
const description = ref('')
const isPrivate = ref(false)
const submitting = ref(false)
const detail = ref('')
const fields = ref({})

async function onSubmit() {
  submitting.value = true
  detail.value = ''
  fields.value = {}

  try {
    const space = await spaceService.createSpace({
      name: name.value,
      description: description.value,
      is_private: isPrivate.value,
    })

    // The creator is made a member on save, so the sidebar needs a refresh.
    await userStore.fetchMemberSpaces()
    await router.push({ name: 'space', params: { slug: space.slug } })
  } catch (error) {
    const parsed = parseApiError(error, 'Could not create the space.')
    detail.value = parsed.detail
    fields.value = parsed.fields
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Card class="mx-auto w-full max-w-2xl">
    <form @submit.prevent="onSubmit">
      <CardHeader>
        <CardTitle>Create a space</CardTitle>
        <CardDescription>Spaces are where posts live. You moderate the ones you create.</CardDescription>
      </CardHeader>

      <CardContent class="flex flex-col gap-4 pt-6">
        <Alert v-if="detail" variant="destructive">
          <AlertDescription>{{ detail }}</AlertDescription>
        </Alert>

        <div class="grid gap-2">
          <Label for="name">Name</Label>
          <Input
            id="name"
            v-model="name"
            maxlength="255"
            required
            :aria-invalid="Boolean(firstError(fields, 'name'))"
          />
          <p v-if="firstError(fields, 'name')" class="text-sm text-destructive">
            {{ firstError(fields, 'name') }}
          </p>
        </div>

        <div class="grid gap-2">
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            v-model="description"
            rows="4"
            :aria-invalid="Boolean(firstError(fields, 'description'))"
          />
          <p v-if="firstError(fields, 'description')" class="text-sm text-destructive">
            {{ firstError(fields, 'description') }}
          </p>
        </div>

        <div class="flex items-start gap-3">
          <Checkbox id="is-private" v-model="isPrivate" class="mt-0.5" />
          <div class="grid gap-1">
            <Label for="is-private">Make this space private</Label>
            <p class="text-sm text-muted-foreground">
              Private spaces are invitation only — nobody can join on their own.
            </p>
          </div>
        </div>
      </CardContent>

      <CardFooter class="mt-6 justify-end gap-2">
        <Button type="button" variant="ghost" @click="router.back()">Cancel</Button>
        <Button type="submit" :disabled="submitting">
          {{ submitting ? 'Creating…' : 'Create space' }}
        </Button>
      </CardFooter>
    </form>
  </Card>
</template>
