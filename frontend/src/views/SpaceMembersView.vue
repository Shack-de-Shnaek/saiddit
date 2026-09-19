<script setup>
import { onMounted, ref, watch } from 'vue'
import { ArrowLeft, Shield } from '@lucide/vue'
import spaceService from '@/services/spaceService'
import { parseApiError } from '@/lib/apiError'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'

const props = defineProps({
  slug: { type: String, required: true },
})

const members = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''

  try {
    members.value = await spaceService.listMembers(props.slug)
  } catch (err) {
    members.value = []
    error.value = parseApiError(err, 'Those members could not be loaded.').detail
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.slug, load)
</script>

<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-4">
    <Button as-child variant="ghost" size="sm" class="self-start">
      <RouterLink :to="{ name: 'space', params: { slug } }">
        <ArrowLeft class="size-4" />
        Back to the space
      </RouterLink>
    </Button>

    <Card>
      <CardHeader>
        <CardTitle>Members</CardTitle>
        <CardDescription v-if="!loading && !error">
          {{ members.length }} member{{ members.length === 1 ? '' : 's' }} of {{ slug }}.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Alert v-if="error" variant="destructive">
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <div v-else-if="loading" class="flex flex-col gap-3">
          <Skeleton v-for="n in 5" :key="n" class="h-6 w-56" />
        </div>

        <p v-else-if="!members.length" class="text-sm text-muted-foreground">
          This space has no members.
        </p>

        <ul v-else class="flex flex-col">
          <li v-for="(member, index) in members" :key="member.id">
            <Separator v-if="index" />
            <div class="flex items-center justify-between py-3">
              <span class="text-sm font-medium">{{ member.user.username }}</span>
              <Badge v-if="member.is_moderator" variant="secondary" class="gap-1">
                <Shield class="size-3" />
                Moderator
              </Badge>
            </div>
          </li>
        </ul>
      </CardContent>
    </Card>
  </div>
</template>
