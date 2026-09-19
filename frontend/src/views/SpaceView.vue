<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { LogIn, LogOut, Lock, Plus, Users } from '@lucide/vue'
import spaceService from '@/services/spaceService'
import { parseApiError } from '@/lib/apiError'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { useUserStore } from '@/stores/user'
import PostListItem from '@/components/posts/PostListItem.vue'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const props = defineProps({
  slug: { type: String, required: true },
})

const router = useRouter()
const userStore = useUserStore()

const space = ref(null)
const spaceError = ref('')
const loadingSpace = ref(true)

const posts = ref([])
const page = ref(0)
const total = ref(0)
const loadingPosts = ref(false)
const exhausted = ref(false)
const postsError = ref('')

// The sentinel below the list; seeing it is what asks for the next page.
const sentinel = ref(null)

async function loadSpace() {
  loadingSpace.value = true
  spaceError.value = ''

  try {
    space.value = await spaceService.getSpace(props.slug)
  } catch (error) {
    space.value = null
    spaceError.value = parseApiError(error, 'That space could not be loaded.').detail
  } finally {
    loadingSpace.value = false
  }
}

async function loadMorePosts() {
  if (loadingPosts.value || exhausted.value || spaceError.value) return

  loadingPosts.value = true
  postsError.value = ''
  const next = page.value + 1

  try {
    const { items, count } = await spaceService.listSpacePosts(props.slug, { page: next })

    page.value = next
    total.value = count
    posts.value.push(...items)

    // An empty page, or having them all, means there is nothing left to ask for.
    if (items.length === 0 || posts.value.length >= count) exhausted.value = true
  } catch (error) {
    postsError.value = parseApiError(error, 'Could not load any more posts.').detail
    // Stop the observer from retrying the same failing page on every scroll.
    exhausted.value = true
  } finally {
    loadingPosts.value = false
  }
}

const isMember = computed(() =>
  Boolean(space.value) && userStore.spaces.some((member) => member.id === space.value.id),
)

// Mirrors Space.allows_contributions_from: anyone signed in may post in a
// public space, private ones need membership.
const canPost = computed(() => {
  if (!space.value || !userStore.isAuthenticated) return false
  return !space.value.is_private || isMember.value
})

// Private spaces are invitation only, so only public ones offer a join.
const canJoin = computed(
  () => Boolean(space.value) && userStore.isAuthenticated && !space.value.is_private && !isMember.value,
)

// The backend refuses to let the creator leave their own space.
const canLeave = computed(
  () => isMember.value && space.value.created_by !== userStore.user?.id,
)

const togglingMembership = ref(false)
const membershipError = ref('')

async function onJoin() {
  togglingMembership.value = true
  membershipError.value = ''

  try {
    await spaceService.joinSpace(props.slug)
    // Membership is read from the store, which the sidebar shares.
    await userStore.fetchMemberSpaces()
  } catch (error) {
    membershipError.value = parseApiError(error, 'Could not join the space.').detail
  } finally {
    togglingMembership.value = false
  }
}

async function onLeave() {
  togglingMembership.value = true
  membershipError.value = ''

  try {
    await spaceService.leaveSpace(props.slug)
    await userStore.fetchMemberSpaces()

    // A private space is no longer visible once you are out of it.
    if (space.value.is_private) await router.push({ name: 'home' })
  } catch (error) {
    membershipError.value = parseApiError(error, 'Could not leave the space.').detail
  } finally {
    togglingMembership.value = false
  }
}

function reset() {
  space.value = null
  membershipError.value = ''
  posts.value = []
  page.value = 0
  total.value = 0
  exhausted.value = false
  postsError.value = ''

  loadSpace()
  loadMorePosts()
}

useInfiniteScroll(sentinel, loadMorePosts)

onMounted(reset)
// Navigating straight from one space to another reuses this component.
watch(() => props.slug, reset)
</script>

<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-4 pb-20">
    <!-- The bottom padding keeps the floating button off the end of the list. -->
    <Alert v-if="spaceError" variant="destructive">
      <AlertDescription>{{ spaceError }}</AlertDescription>
    </Alert>

    <Card v-else-if="loadingSpace">
      <CardHeader class="gap-2">
        <Skeleton class="h-6 w-48" />
        <Skeleton class="h-4 w-full max-w-md" />
      </CardHeader>
    </Card>

    <Card v-else-if="space">
      <CardHeader>
        <CardTitle class="flex items-center gap-2 text-2xl">
          {{ space.name }}
          <Badge v-if="space.is_private" variant="secondary" class="gap-1">
            <Lock class="size-3" />
            Private
          </Badge>
        </CardTitle>
        <CardDescription v-if="space.description">{{ space.description }}</CardDescription>
        <CardDescription v-else class="italic">No description yet.</CardDescription>
      </CardHeader>

      <CardContent class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center gap-2">
          <Button as-child variant="outline" size="sm">
            <RouterLink :to="{ name: 'space-members', params: { slug: space.slug } }">
              <Users class="size-4" />
              Members
            </RouterLink>
          </Button>

          <Button v-if="canJoin" size="sm" :disabled="togglingMembership" @click="onJoin">
            <LogIn class="size-4" />
            {{ togglingMembership ? 'Joining…' : 'Join' }}
          </Button>

          <Button
            v-else-if="canLeave"
            variant="outline"
            size="sm"
            :disabled="togglingMembership"
            @click="onLeave"
          >
            <LogOut class="size-4" />
            {{ togglingMembership ? 'Leaving…' : 'Leave' }}
          </Button>
        </div>

        <Alert v-if="membershipError" variant="destructive">
          <AlertDescription>{{ membershipError }}</AlertDescription>
        </Alert>
      </CardContent>
    </Card>

    <template v-if="!spaceError">
      <PostListItem v-for="post in posts" :key="post.id" :post="post" />

      <!-- Only meaningful once the first page has settled. -->
      <p v-if="!loadingPosts && !posts.length && exhausted" class="py-8 text-center text-sm text-muted-foreground">
        No posts here yet.
      </p>

      <template v-if="loadingPosts">
        <Skeleton v-for="n in 3" :key="n" class="h-20 w-full rounded-xl" />
      </template>

      <Alert v-if="postsError" variant="destructive">
        <AlertDescription>{{ postsError }}</AlertDescription>
      </Alert>

      <!-- Kept out of the DOM once there is nothing left, so it stops firing. -->
      <div v-if="!exhausted" ref="sentinel" aria-hidden="true" class="h-px" />

      <p v-else-if="posts.length" class="py-6 text-center text-sm text-muted-foreground">
        That's all {{ total }} post{{ total === 1 ? '' : 's' }}.
      </p>
    </template>

    <Button
      v-if="canPost"
      as-child
      size="lg"
      class="fixed right-6 bottom-6 z-20 rounded-full shadow-lg"
    >
      <RouterLink :to="{ name: 'post-create', params: { slug: space.slug } }">
        <Plus class="size-5" />
        Create post
      </RouterLink>
    </Button>
  </div>
</template>
