<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { Lock } from '@lucide/vue'
import spaceService from '@/services/spaceService'
import {
  Combobox,
  ComboboxAnchor,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  ComboboxViewport,
} from '@/components/ui/combobox'

const RESULT_LIMIT = 8

const router = useRouter()

const term = ref('')
const results = ref([])
const loading = ref(false)
const failed = ref(false)

// Only the latest request may write results, so a slow earlier one can't
// overwrite what the visitor is typing now.
let latestRequest = 0

const runSearch = useDebounceFn(async (query) => {
  const request = ++latestRequest

  try {
    const { items } = await spaceService.searchSpaces(query, { pageSize: RESULT_LIMIT })
    if (request === latestRequest) results.value = items
  } catch {
    if (request === latestRequest) failed.value = true
  } finally {
    if (request === latestRequest) loading.value = false
  }
}, 250)

watch(term, (value) => {
  const query = value.trim()
  failed.value = false

  if (!query) {
    // Invalidate anything still in flight; the endpoint rejects blank queries.
    latestRequest++
    results.value = []
    loading.value = false
    return
  }

  loading.value = true
  runSearch(query)
})

function onSelect(slug) {
  if (!slug) return
  term.value = ''
  router.push(`/spaces/${slug}`)
}
</script>

<template>
  <!-- The server already filters, so the combobox shouldn't filter again. -->
  <Combobox
    :model-value="null"
    ignore-filter
    class="mx-auto w-full max-w-md"
    @update:model-value="onSelect"
  >
    <ComboboxAnchor
      class="w-full overflow-hidden rounded-full border bg-muted [&>[data-slot=command-input-wrapper]]:border-0"
    >
      <ComboboxInput v-model="term" placeholder="Search spaces" aria-label="Search spaces" />
    </ComboboxAnchor>

    <ComboboxList v-if="term.trim()" class="w-(--reka-combobox-trigger-width)">
      <ComboboxViewport class="p-1">
        <ComboboxEmpty class="py-4 text-muted-foreground">
          <template v-if="loading">Searching…</template>
          <template v-else-if="failed">Search failed. Please try again.</template>
          <template v-else>No spaces found.</template>
        </ComboboxEmpty>

        <ComboboxItem
          v-for="space in results"
          :key="space.id"
          :value="space.slug"
          :text-value="space.name"
        >
          <span class="truncate">{{ space.name }}</span>
          <Lock v-if="space.is_private" class="ml-auto size-3.5" aria-label="Private" />
        </ComboboxItem>
      </ComboboxViewport>
    </ComboboxList>
  </Combobox>
</template>
