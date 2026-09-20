<script setup>
import { computed } from 'vue'
import { ArrowUpDown } from '@lucide/vue'
import { POST_SORTS } from '@/composables/usePostList'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// Bound to the `sort` of a usePostList listing; changing it reloads the list.
const sort = defineModel({ type: String, required: true })

// Clearing the select would leave the listing without an order to ask for, so
// picking the current choice again is a no-op rather than an empty value.
const selected = computed({
  get: () => sort.value,
  set: (value) => {
    if (value) sort.value = value
  },
})
</script>

<template>
  <Select v-model="selected">
    <SelectTrigger size="sm" class="w-36" aria-label="Sort posts">
      <ArrowUpDown class="size-4" />
      <SelectValue />
    </SelectTrigger>

    <SelectContent align="end">
      <SelectItem v-for="option in POST_SORTS" :key="option.value" :value="option.value">
        {{ option.label }}
      </SelectItem>
    </SelectContent>
  </Select>
</template>
