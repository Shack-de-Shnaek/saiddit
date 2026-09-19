<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowBigDown, ArrowBigUp } from '@lucide/vue'
import postService from '@/services/postService'
import { useUserStore } from '@/stores/user'
import { parseApiError } from '@/lib/apiError'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const props = defineProps({
  // 'post' or 'comment'; decides which pair of endpoints to call.
  targetType: {
    type: String,
    required: true,
    validator: (value) => ['post', 'comment'].includes(value),
  },
  targetId: { type: Number, required: true },
  score: { type: Number, default: 0 },
  // The viewer's own vote: 1, -1 or 0.
  myVote: { type: Number, default: 0 },
  orientation: { type: String, default: 'vertical' },
})

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// Held locally so a vote shows immediately; the props re-seed it if the
// parent reloads the row.
const score = ref(props.score)
const myVote = ref(props.myVote)
const pending = ref(false)
const error = ref('')

watch(
  () => [props.score, props.myVote],
  ([nextScore, nextVote]) => {
    score.value = nextScore
    myVote.value = nextVote
  },
)

const isPost = computed(() => props.targetType === 'post')

async function send(value) {
  if (isPost.value) return postService.voteOnPost(props.targetId, value)
  return postService.voteOnComment(props.targetId, value)
}

async function remove() {
  if (isPost.value) return postService.unvotePost(props.targetId)
  return postService.unvoteComment(props.targetId)
}

async function cast(value) {
  if (!userStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }

  if (pending.value) return

  const previousVote = myVote.value
  const previousScore = score.value
  // Clicking the arrow you already chose takes the vote back.
  const next = previousVote === value ? 0 : value

  myVote.value = next
  score.value = previousScore - previousVote + next
  pending.value = true
  error.value = ''

  try {
    if (next === 0) {
      await remove()
    } else {
      await send(next)
    }
  } catch (err) {
    // The server refused it, so put the row back the way it was.
    myVote.value = previousVote
    score.value = previousScore
    error.value = parseApiError(err, 'Your vote did not go through.').detail
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div
    :class="cn(
      'flex items-center gap-0.5',
      orientation === 'vertical' ? 'flex-col' : 'flex-row',
    )"
  >
    <Button
      variant="ghost"
      size="icon-sm"
      :aria-label="`Upvote (score ${score})`"
      :aria-pressed="myVote === 1"
      :class="myVote === 1 ? 'text-primary' : 'text-muted-foreground'"
      @click="cast(1)"
    >
      <ArrowBigUp :class="myVote === 1 ? 'fill-current' : ''" />
    </Button>

    <span class="min-w-6 text-center text-sm font-medium tabular-nums">{{ score }}</span>

    <Button
      variant="ghost"
      size="icon-sm"
      :aria-label="`Downvote (score ${score})`"
      :aria-pressed="myVote === -1"
      :class="myVote === -1 ? 'text-destructive' : 'text-muted-foreground'"
      @click="cast(-1)"
    >
      <ArrowBigDown :class="myVote === -1 ? 'fill-current' : ''" />
    </Button>

    <p v-if="error" class="text-xs text-destructive">{{ error }}</p>
  </div>
</template>
