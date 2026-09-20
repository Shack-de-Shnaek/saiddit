<script setup>
import { computed, onMounted, ref } from 'vue'
import { Plus } from '@lucide/vue'
import postService from '@/services/postService'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { usePostList } from '@/composables/usePostList'
import { useUserStore } from '@/stores/user'
import PostListItem from '@/components/posts/PostListItem.vue'
import PostSortSelect from '@/components/posts/PostSortSelect.vue'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const userStore = useUserStore()

const {
  posts,
  sort,
  total,
  loading,
  exhausted,
  error,
  loadMore,
  reset,
} = usePostList(({ sort: order, page }) => postService.listFeed({ sort: order, page }))

// The sentinel below the list; seeing it is what asks for the next page.
const sentinel = ref(null)

// The feed follows memberships, so say whose it is.
const subtitle = computed(() =>
  userStore.isAuthenticated
    ? 'Posts from the spaces you are a member of.'
    : 'Posts from the public spaces. Sign in to follow your own.',
)

// Nothing to show and nowhere it could have come from: the answer is to go
// join a space, not to wait for posts.
const emptyBecauseNoSpaces = computed(
  () => userStore.isAuthenticated && !posts.value.length && !userStore.spaces.length,
)

useInfiniteScroll(sentinel, loadMore)

onMounted(reset)
</script>

<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-4 pb-6">
    <Card>
      <CardHeader>
        <CardTitle class="text-2xl">Home</CardTitle>
        <CardDescription>{{ subtitle }}</CardDescription>
      </CardHeader>
    </Card>

    <div class="flex items-center justify-between gap-2">
      <h2 class="text-sm font-medium text-muted-foreground">Feed</h2>
      <PostSortSelect v-model="sort" />
    </div>

    <PostListItem v-for="post in posts" :key="post.id" :post="post" show-space />

    <!-- Only meaningful once the first page has settled. -->
    <template v-if="!loading && !posts.length && exhausted">
      <Card v-if="emptyBecauseNoSpaces">
        <CardContent class="flex flex-col items-start gap-3 text-sm text-muted-foreground">
          You are not a member of any space yet, so there is nothing to feed you.
          Search at the top to find one to join, or start your own.
          <Button as-child variant="outline" size="sm">
            <RouterLink :to="{ name: 'space-create' }">
              <Plus class="size-4" />
              Create a space
            </RouterLink>
          </Button>
        </CardContent>
      </Card>

      <p v-else class="py-8 text-center text-sm text-muted-foreground">
        No posts to show yet.
      </p>
    </template>

    <template v-if="loading">
      <Skeleton v-for="n in 3" :key="n" class="h-20 w-full rounded-xl" />
    </template>

    <Alert v-if="error" variant="destructive">
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Kept out of the DOM once there is nothing left, so it stops firing. -->
    <div v-if="!exhausted" ref="sentinel" aria-hidden="true" class="h-px" />

    <p v-else-if="posts.length" class="py-6 text-center text-sm text-muted-foreground">
      That's all {{ total }} post{{ total === 1 ? '' : 's' }}.
    </p>
  </div>
</template>
