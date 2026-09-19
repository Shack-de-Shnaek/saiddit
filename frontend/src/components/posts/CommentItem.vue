<script setup>
import { ref } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import { Reply } from '@lucide/vue'
import postService from '@/services/postService'
import { useUserStore } from '@/stores/user'
import { parseApiError, firstError } from '@/lib/apiError'
import { formatDate } from '@/lib/format'
import VoteButtons from '@/components/posts/VoteButtons.vue'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

const props = defineProps({
  comment: { type: Object, required: true },
})

const userStore = useUserStore()

const replies = ref([])
const loadingReplies = ref(false)
const repliesError = ref('')

// The comment's own body, not its whole subtree, so a reply scrolling past
// doesn't count as this comment being seen.
const body = ref(null)

async function loadReplies() {
  loadingReplies.value = true
  repliesError.value = ''

  try {
    const { items } = await postService.listReplies(props.comment.id)
    replies.value = items
  } catch (error) {
    repliesError.value = parseApiError(error, 'Could not load the replies.').detail
  } finally {
    loadingReplies.value = false
  }
}

const replying = ref(false)
const draft = ref('')
const submitting = ref(false)
const submitDetail = ref('')
const submitFields = ref({})

function closeReply() {
  replying.value = false
  draft.value = ''
  submitDetail.value = ''
  submitFields.value = {}
}

async function onSubmitReply() {
  submitting.value = true
  submitDetail.value = ''
  submitFields.value = {}

  try {
    const reply = await postService.replyToComment(props.comment.id, draft.value)

    // Replies are listed newest first, so a new one goes on top of this
    // comment's replies. The create response has neither reply_count nor
    // my_vote; a brand new reply has no replies and no vote of yours.
    replies.value.unshift({ ...reply, reply_count: 0, my_vote: 0 })
    closeReply()
  } catch (error) {
    const parsed = parseApiError(error, 'Could not post the reply.')
    submitDetail.value = parsed.detail
    submitFields.value = parsed.fields
  } finally {
    submitting.value = false
  }
}

// Replies are fetched once, the first time the comment comes into view. Each
// reply is a CommentItem too, so this walks the tree as the reader scrolls.
const { stop } = useIntersectionObserver(body, ([entry]) => {
  if (!entry?.isIntersecting) return
  stop()

  // reply_count says up front whether there is anything to ask for.
  if (props.comment.reply_count > 0) loadReplies()
})
</script>

<template>
  <div class="flex flex-col gap-3">
    <div ref="body" class="flex flex-col gap-1">
      <p class="text-xs text-muted-foreground">
        <span class="font-medium text-foreground">{{ comment.author?.username ?? '[deleted]' }}</span>
        · {{ formatDate(comment.created_at) }}
      </p>
      <p class="whitespace-pre-wrap text-sm">{{ comment.content }}</p>
      <div class="-ml-2 flex items-center gap-1">
        <VoteButtons
          target-type="comment"
          :target-id="comment.id"
          :score="comment.score"
          :my-vote="comment.my_vote"
          orientation="horizontal"
        />
        <!-- Held back while replies load, so the fetch can't overwrite a new one. -->
        <Button
          v-if="userStore.isAuthenticated && !replying"
          variant="ghost"
          size="sm"
          class="h-7 text-muted-foreground"
          :disabled="loadingReplies"
          @click="replying = true"
        >
          <Reply class="size-4" />
          Reply
        </Button>
      </div>
    </div>

    <form v-if="replying" class="flex flex-col gap-2 border-l pl-4" @submit.prevent="onSubmitReply">
      <Alert v-if="submitDetail" variant="destructive">
        <AlertDescription>{{ submitDetail }}</AlertDescription>
      </Alert>

      <Label :for="`reply-${comment.id}`" class="sr-only">
        Reply to {{ comment.author?.username ?? '[deleted]' }}
      </Label>
      <Textarea
        :id="`reply-${comment.id}`"
        v-model="draft"
        rows="3"
        required
        :placeholder="`Reply to ${comment.author?.username ?? '[deleted]'}`"
        :aria-invalid="Boolean(firstError(submitFields, 'content'))"
      />
      <p v-if="firstError(submitFields, 'content')" class="text-sm text-destructive">
        {{ firstError(submitFields, 'content') }}
      </p>

      <div class="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" @click="closeReply">Cancel</Button>
        <Button type="submit" size="sm" :disabled="submitting || !draft.trim()">
          {{ submitting ? 'Replying…' : 'Reply' }}
        </Button>
      </div>
    </form>

    <div v-if="replies.length || loadingReplies || repliesError" class="flex flex-col gap-4 border-l pl-4">
      <CommentItem v-for="reply in replies" :key="reply.id" :comment="reply" />

      <div v-if="loadingReplies" class="flex flex-col gap-2">
        <Skeleton class="h-3 w-32" />
        <Skeleton class="h-4 w-full max-w-sm" />
      </div>

      <p v-if="repliesError" class="text-sm text-destructive">{{ repliesError }}</p>
    </div>
  </div>
</template>
