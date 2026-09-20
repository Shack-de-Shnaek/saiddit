import { ref, watch } from 'vue'
import { parseApiError } from '@/lib/apiError'

// The sort orders the API accepts on a post listing, in the order they are
// offered in the UI. The values match the backend's `sort` query parameter.
export const POST_SORTS = [
  { value: 'new', label: 'Newest' },
  { value: 'old', label: 'Oldest' },
  { value: 'votes', label: 'Top voted' },
]

// A paged, sortable post listing, shared by the home feed and a space page.
// `fetchPage` is given { sort, page } and resolves to { items, count }, which
// is what the paginated endpoints answer with.
//
// Changing `sort` throws the loaded pages away and starts the listing again,
// since page 2 of one order has nothing to do with page 2 of another.
export function usePostList(fetchPage, { initialSort = 'new' } = {}) {
  const posts = ref([])
  const sort = ref(initialSort)
  const page = ref(0)
  const total = ref(0)
  const loading = ref(false)
  const exhausted = ref(false)
  const error = ref('')

  // Bumped by every reset, so a page still in flight can tell that the list it
  // was fetched for is gone and drop its result instead of appending to the new one.
  let generation = 0

  async function loadMore() {
    if (loading.value || exhausted.value) return

    const run = generation
    const next = page.value + 1

    loading.value = true
    error.value = ''

    try {
      const { items, count } = await fetchPage({ sort: sort.value, page: next })

      if (run !== generation) return

      page.value = next
      total.value = count
      posts.value.push(...items)

      // An empty page, or having them all, means there is nothing left to ask for.
      if (items.length === 0 || posts.value.length >= count) exhausted.value = true
    } catch (requestError) {
      if (run !== generation) return

      error.value = parseApiError(requestError, 'Could not load any more posts.').detail
      // Stop the observer from retrying the same failing page on every scroll.
      exhausted.value = true
    } finally {
      if (run === generation) loading.value = false
    }
  }

  // Back to an empty list and the first page; also loads it.
  function reset() {
    generation += 1
    posts.value = []
    page.value = 0
    total.value = 0
    exhausted.value = false
    error.value = ''
    loading.value = false

    return loadMore()
  }

  watch(sort, reset)

  return { posts, sort, total, loading, exhausted, error, loadMore, reset }
}
