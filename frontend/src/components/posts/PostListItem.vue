<script setup>
import { computed } from 'vue'
import { Images, MessageSquare } from '@lucide/vue'
import { formatDate } from '@/lib/format'
import VoteButtons from '@/components/posts/VoteButtons.vue'
import { Card } from '@/components/ui/card'

const props = defineProps({
  post: { type: Object, required: true },
  // The space page already says which space you are in.
  showSpace: { type: Boolean, default: false },
})

const images = computed(() => props.post.images ?? [])
// Only the first one gets a thumbnail; the rest are counted on top of it.
const thumbnail = computed(() => images.value[0] ?? null)
</script>

<template>
  <RouterLink
    :to="{ name: 'post', params: { id: post.id } }"
    class="block rounded-xl outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
  >
    <Card class="flex-row items-start gap-4 p-4 transition-colors hover:bg-accent/50">
      <!-- Inside the card's link, so the arrows must not navigate. -->
      <div class="shrink-0" @click.stop.prevent>
        <VoteButtons
          target-type="post"
          :target-id="post.id"
          :score="post.score"
          :my-vote="post.my_vote"
        />
      </div>

      <div class="min-w-0 flex-1">
        <h3 class="truncate font-medium">{{ post.title }}</h3>
        <p class="mt-1 text-xs text-muted-foreground">
          <template v-if="showSpace && post.space">{{ post.space.name }} · </template>
          {{ post.author?.username ?? '[deleted]' }} · {{ formatDate(post.created_at) }}
          <template v-if="images.length">
            · <Images class="inline size-3 align-text-bottom" /> {{ images.length }}
          </template>
        </p>
      </div>

      <div v-if="thumbnail" class="relative size-20 shrink-0 overflow-hidden rounded-md border bg-muted">
        <img :src="thumbnail.image" :alt="post.title" loading="lazy" class="size-full object-cover" />
        <span
          v-if="images.length > 1"
          class="absolute right-1 bottom-1 rounded bg-background/80 px-1 text-xs font-medium"
        >
          +{{ images.length - 1 }}
        </span>
      </div>

      <div
        class="flex shrink-0 items-center gap-1 self-center text-sm text-muted-foreground"
        :aria-label="`${post.comment_count} comment${post.comment_count === 1 ? '' : 's'}`"
      >
        <MessageSquare class="size-4" />
        {{ post.comment_count }}
      </div>
    </Card>
  </RouterLink>
</template>
