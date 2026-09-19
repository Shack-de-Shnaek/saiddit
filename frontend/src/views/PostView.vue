<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, MessageSquarePlus } from '@lucide/vue'
import postService from '@/services/postService'
import { useUserStore } from '@/stores/user'
import { parseApiError, firstError } from '@/lib/apiError'
import { formatDate } from '@/lib/format'
import CommentItem from '@/components/posts/CommentItem.vue'
import VoteButtons from '@/components/posts/VoteButtons.vue'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

const props = defineProps({
  id: { type: Number, required: true },
})

const route = useRoute()
const userStore = useUserStore()

const post = ref(null)
const loading = ref(true)
const error = ref('')

const comments = ref([])
const commentCount = ref(0)
const loadingComments = ref(true)
const commentsError = ref('')

const composing = ref(false)
const draft = ref('')
const submitting = ref(false)
const submitDetail = ref('')
const submitFields = ref({})

async function load() {
  loading.value = true
  error.value = ''

  try {
    post.value = await postService.getPost(props.id)
  } catch (err) {
    post.value = null
    error.value = parseApiError(err, 'That post could not be loaded.').detail
  } finally {
    loading.value = false
  }
}

// Only the first page; each comment fetches its own replies once it is seen.
async function loadComments() {
  loadingComments.value = true
  commentsError.value = ''

  try {
    const { items, count } = await postService.listComments(props.id)
    comments.value = items
    commentCount.value = count
  } catch (err) {
    comments.value = []
    commentsError.value = parseApiError(err, 'Could not load the comments.').detail
  } finally {
    loadingComments.value = false
  }
}

function closeComposer() {
  composing.value = false
  draft.value = ''
  submitDetail.value = ''
  submitFields.value = {}
}

async function onSubmitComment() {
  submitting.value = true
  submitDetail.value = ''
  submitFields.value = {}

  try {
    const comment = await postService.addComment(props.id, draft.value)

    // Comments are listed newest first, so a new one goes on top. The create
    // response has no reply_count; a brand new comment has no replies.
    comments.value.unshift({ ...comment, reply_count: 0 })
    commentCount.value += 1
    closeComposer()
  } catch (err) {
    const parsed = parseApiError(err, 'Could not add the comment.')
    submitDetail.value = parsed.detail
    submitFields.value = parsed.fields
  } finally {
    submitting.value = false
  }
}

function reset() {
  closeComposer()
  load()
  loadComments()
}

onMounted(reset)
// Navigating straight from one post to another reuses this component.
watch(() => props.id, reset)
</script>

<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-4">
    <Button v-if="post?.space" as-child variant="ghost" size="sm" class="self-start">
      <RouterLink :to="{ name: 'space', params: { slug: post.space.slug } }">
        <ArrowLeft class="size-4" />
        {{ post.space.name }}
      </RouterLink>
    </Button>

    <Alert v-if="error" variant="destructive">
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <Card v-else-if="loading">
      <CardHeader class="gap-2">
        <Skeleton class="h-7 w-2/3" />
        <Skeleton class="h-4 w-40" />
      </CardHeader>
      <CardContent class="flex flex-col gap-2">
        <Skeleton class="h-4 w-full" />
        <Skeleton class="h-4 w-5/6" />
      </CardContent>
    </Card>

    <Card v-else-if="post">
      <CardHeader>
        <div class="flex items-start gap-4">
          <VoteButtons
            class="shrink-0"
            target-type="post"
            :target-id="post.id"
            :score="post.score"
            :my-vote="post.my_vote"
          />

          <div class="min-w-0 flex-1">
            <CardTitle class="text-2xl">{{ post.title }}</CardTitle>
            <CardDescription class="mt-1">
              {{ post.author?.username ?? '[deleted]' }} · {{ formatDate(post.created_at) }}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent class="flex flex-col gap-4">
        <p class="whitespace-pre-wrap text-sm">{{ post.content }}</p>

        <figure v-for="image in post.images" :key="image.id" class="overflow-hidden rounded-lg border bg-muted">
          <img :src="image.image" :alt="post.title" loading="lazy" class="w-full object-contain" />
        </figure>
      </CardContent>
    </Card>

    <Card v-if="post">
      <CardHeader class="flex flex-row items-center justify-between gap-4">
        <CardTitle>Comments ({{ commentCount }})</CardTitle>

        <template v-if="userStore.loaded && !composing">
          <Button v-if="userStore.isAuthenticated" size="sm" @click="composing = true">
            <MessageSquarePlus class="size-4" />
            Add comment
          </Button>
          <Button v-else as-child variant="outline" size="sm">
            <RouterLink :to="{ name: 'login', query: { redirect: route.fullPath } }">
              Log in to comment
            </RouterLink>
          </Button>
        </template>
      </CardHeader>

      <CardContent class="flex flex-col gap-4">
        <form v-if="composing" class="flex flex-col gap-2" @submit.prevent="onSubmitComment">
          <Alert v-if="submitDetail" variant="destructive">
            <AlertDescription>{{ submitDetail }}</AlertDescription>
          </Alert>

          <Label for="comment" class="sr-only">Comment</Label>
          <Textarea
            id="comment"
            v-model="draft"
            rows="4"
            required
            placeholder="What are your thoughts?"
            :aria-invalid="Boolean(firstError(submitFields, 'content'))"
          />
          <p v-if="firstError(submitFields, 'content')" class="text-sm text-destructive">
            {{ firstError(submitFields, 'content') }}
          </p>

          <div class="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" @click="closeComposer">Cancel</Button>
            <Button type="submit" size="sm" :disabled="submitting || !draft.trim()">
              {{ submitting ? 'Commenting…' : 'Comment' }}
            </Button>
          </div>

          <Separator class="mt-2" />
        </form>

        <Alert v-if="commentsError" variant="destructive">
          <AlertDescription>{{ commentsError }}</AlertDescription>
        </Alert>

        <div v-else-if="loadingComments" class="flex flex-col gap-2">
          <Skeleton class="h-3 w-32" />
          <Skeleton class="h-4 w-full max-w-md" />
        </div>

        <p v-else-if="comments.length === 0" class="text-sm text-muted-foreground">
          No comments yet.
        </p>

        <template v-for="(comment, index) in comments" v-else :key="comment.id">
          <Separator v-if="index > 0" />
          <CommentItem :comment="comment" />
        </template>
      </CardContent>
    </Card>
  </div>
</template>
