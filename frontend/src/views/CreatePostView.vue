<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ImagePlus, X } from '@lucide/vue'
import spaceService from '@/services/spaceService'
import postService from '@/services/postService'
import { parseApiError, firstError } from '@/lib/apiError'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

// Matches MAX_POST_IMAGES / MAX_IMAGE_BYTES on the API.
const MAX_IMAGES = 10
const MAX_IMAGE_BYTES = 10 * 1024 * 1024

const props = defineProps({
  slug: { type: String, required: true },
})

const router = useRouter()

const title = ref('')
const content = ref('')
// { file, url } pairs; url is an object URL for the preview.
const attachments = ref([])
const fileInput = ref(null)

const submitting = ref(false)
const detail = ref('')
const fields = ref({})
// Set when the post exists but its images did not go up, so a retry uploads
// the images instead of creating the post twice.
const createdPost = ref(null)

const remaining = computed(() => MAX_IMAGES - attachments.value.length)

function addFiles(event) {
  const chosen = Array.from(event.target.files ?? [])
  fields.value = {}

  for (const file of chosen) {
    if (attachments.value.length >= MAX_IMAGES) {
      fields.value = { images: [`A post can have at most ${MAX_IMAGES} images.`] }
      break
    }

    if (!file.type.startsWith('image/')) {
      fields.value = { images: [`${file.name} is not an image.`] }
      continue
    }

    if (file.size > MAX_IMAGE_BYTES) {
      fields.value = { images: [`${file.name} is larger than the 10 MB limit.`] }
      continue
    }

    attachments.value.push({ file, url: URL.createObjectURL(file) })
  }

  // Let the same file be picked again after it has been removed.
  event.target.value = ''
}

function removeAttachment(index) {
  const [removed] = attachments.value.splice(index, 1)
  URL.revokeObjectURL(removed.url)
}

onBeforeUnmount(() => {
  for (const attachment of attachments.value) URL.revokeObjectURL(attachment.url)
})

async function onSubmit() {
  submitting.value = true
  detail.value = ''
  fields.value = {}

  try {
    // Skipped on a retry: the post is already there, only the images failed.
    if (!createdPost.value) {
      createdPost.value = await spaceService.createSpacePost(props.slug, {
        title: title.value,
        content: content.value,
      })
    }

    if (attachments.value.length) {
      await postService.addImages(
        createdPost.value.id,
        attachments.value.map((attachment) => attachment.file),
      )
    }

    await router.push({ name: 'post', params: { id: createdPost.value.id } })
  } catch (error) {
    const parsed = parseApiError(error, 'Could not publish the post.')
    fields.value = parsed.fields
    detail.value = createdPost.value
      ? `The post was created, but its images were not attached. ${parsed.detail}`
      : parsed.detail
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Card class="mx-auto w-full max-w-2xl">
    <form @submit.prevent="onSubmit">
      <CardHeader>
        <CardTitle>Create a post</CardTitle>
        <CardDescription>Posting to {{ slug }}.</CardDescription>
      </CardHeader>

      <CardContent class="flex flex-col gap-4 pt-6">
        <Alert v-if="detail" variant="destructive">
          <AlertDescription>{{ detail }}</AlertDescription>
        </Alert>

        <div class="grid gap-2">
          <Label for="title">Title</Label>
          <Input
            id="title"
            v-model="title"
            maxlength="255"
            required
            :aria-invalid="Boolean(firstError(fields, 'title'))"
          />
          <p v-if="firstError(fields, 'title')" class="text-sm text-destructive">
            {{ firstError(fields, 'title') }}
          </p>
        </div>

        <div class="grid gap-2">
          <Label for="content">Body</Label>
          <Textarea
            id="content"
            v-model="content"
            rows="8"
            required
            :aria-invalid="Boolean(firstError(fields, 'content'))"
          />
          <p v-if="firstError(fields, 'content')" class="text-sm text-destructive">
            {{ firstError(fields, 'content') }}
          </p>
        </div>

        <div class="grid gap-2">
          <Label>Images</Label>

          <div v-if="attachments.length" class="grid grid-cols-3 gap-2 sm:grid-cols-4">
            <div
              v-for="(attachment, index) in attachments"
              :key="attachment.url"
              class="relative aspect-square overflow-hidden rounded-md border bg-muted"
            >
              <img :src="attachment.url" :alt="attachment.file.name" class="size-full object-cover" />
              <Button
                type="button"
                variant="secondary"
                size="icon-xs"
                class="absolute top-1 right-1"
                :aria-label="`Remove ${attachment.file.name}`"
                @click="removeAttachment(index)"
              >
                <X />
              </Button>
            </div>
          </div>

          <!-- The input itself stays hidden; the button is the control. -->
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            multiple
            class="sr-only"
            @change="addFiles"
          />

          <Button
            type="button"
            variant="outline"
            size="sm"
            class="self-start"
            :disabled="remaining === 0"
            @click="fileInput?.click()"
          >
            <ImagePlus class="size-4" />
            Attach images
          </Button>

          <p v-if="firstError(fields, 'images')" class="text-sm text-destructive">
            {{ firstError(fields, 'images') }}
          </p>
          <p v-else class="text-xs text-muted-foreground">
            {{ remaining }} of {{ MAX_IMAGES }} left · up to 10 MB each.
          </p>
        </div>
      </CardContent>

      <CardFooter class="mt-6 justify-end gap-2">
        <Button type="button" variant="ghost" @click="router.back()">Cancel</Button>
        <Button type="submit" :disabled="submitting">
          {{ submitting ? 'Posting…' : createdPost ? 'Retry images' : 'Post' }}
        </Button>
      </CardFooter>
    </form>
  </Card>
</template>
