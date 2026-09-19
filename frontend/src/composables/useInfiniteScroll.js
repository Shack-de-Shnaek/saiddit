import { onBeforeUnmount, onMounted, watch } from 'vue'

// Runs `onReach` whenever the element `target` points at scrolls into view.
// rootMargin gives the fetch a head start, so the list tops up shortly before
// the reader actually hits the bottom.
export function useInfiniteScroll(target, onReach, { rootMargin = '300px' } = {}) {
  let observer = null

  function disconnect() {
    observer?.disconnect()
    observer = null
  }

  function observe(element) {
    disconnect()

    if (!element) return

    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) onReach()
      },
      { rootMargin },
    )
    observer.observe(element)
  }

  onMounted(() => observe(target.value))
  // The sentinel is behind a v-if, so it comes and goes as the list loads.
  watch(target, observe)
  onBeforeUnmount(disconnect)

  return { disconnect }
}
