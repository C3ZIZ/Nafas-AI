<template>
  <div ref="rootEl" class="relative w-full">
    <button
      type="button"
      :disabled="disabled"
      :aria-haspopup="'listbox'"
      :aria-expanded="open"
      @click="toggle"
      @keydown="onButtonKey"
      :class="[
        'field-input w-full flex items-center justify-between gap-2 cursor-pointer',
        'text-start disabled:cursor-not-allowed disabled:opacity-60',
        open && 'ring-4 ring-brand-500/15 border-brand-500'
      ]">
      <div class="flex items-center gap-2 min-w-0 flex-1">
        <component v-if="selectedOption?.icon"
                   :is="selectedOption.icon"
                   class="h-4 w-4 text-brand-600 shrink-0"
                   :stroke-width="1.75" />
        <div class="min-w-0 flex-1">
          <div v-if="selectedOption" class="truncate font-medium text-ink">
            {{ selectedOption.label }}
          </div>
          <div v-else class="truncate text-ink-subtle">
            {{ placeholder }}
          </div>
          <div v-if="selectedOption?.subtitle && showSubtitle"
               class="text-2xs text-ink-subtle truncate">
            {{ selectedOption.subtitle }}
          </div>
        </div>
      </div>
      <ChevronDown
        class="h-4 w-4 text-ink-muted transition-transform duration-200 shrink-0"
        :class="open && 'rotate-180 text-brand-600'"
        :stroke-width="1.75" />
    </button>

    <!-- Popover -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-1">
      <div
        v-show="open"
        class="absolute z-40 mt-2 w-full min-w-[12rem] bg-surface border border-line rounded-2xl shadow-soft overflow-hidden">
        <ul
          ref="listEl"
          role="listbox"
          tabindex="-1"
          class="max-h-72 overflow-y-auto py-1">
          <li
            v-for="(opt, i) in options"
            :key="opt.value"
            role="option"
            :aria-selected="opt.value === modelValue"
            @click="select(opt)"
            @mouseenter="focusIndex = i"
            :class="[
              'px-3 py-2.5 cursor-pointer flex items-center gap-2.5 text-sm transition-colors duration-100',
              focusIndex === i ? 'bg-brand-50' : 'hover:bg-stone-50',
              opt.value === modelValue && 'bg-brand-50'
            ]">
            <component v-if="opt.icon"
                       :is="opt.icon"
                       class="h-4 w-4 shrink-0"
                       :class="opt.value === modelValue ? 'text-brand-700' : 'text-ink-muted'"
                       :stroke-width="1.75" />
            <div class="min-w-0 flex-1">
              <div :class="[
                'truncate',
                opt.value === modelValue ? 'font-semibold text-brand-900' : 'font-medium text-ink'
              ]">{{ opt.label }}</div>
              <div v-if="opt.subtitle" class="text-2xs text-ink-subtle truncate mt-0.5">
                {{ opt.subtitle }}
              </div>
            </div>
            <Check v-if="opt.value === modelValue"
                   class="h-4 w-4 text-brand-700 shrink-0"
                   :stroke-width="2.5" />
          </li>
          <li v-if="!options.length" class="px-3 py-3 text-sm text-ink-subtle text-center">
            {{ emptyText }}
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ChevronDown, Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: [String, Number, Boolean, null], default: null },
  options: { type: Array, required: true },
  placeholder: { type: String, default: '— select —' },
  emptyText: { type: String, default: 'No options' },
  disabled: { type: Boolean, default: false },
  showSubtitle: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const rootEl = ref(null)
const listEl = ref(null)
const focusIndex = ref(-1)

const selectedOption = computed(() =>
  props.options.find(o => o.value === props.modelValue) || null
)

function toggle() {
  if (props.disabled) return
  open.value = !open.value
  if (open.value) {
    focusIndex.value = props.options.findIndex(o => o.value === props.modelValue)
    if (focusIndex.value < 0) focusIndex.value = 0
    nextTick(scrollFocusedIntoView)
  }
}

function close() { open.value = false }

function select(opt) {
  if (opt.disabled) return
  emit('update:modelValue', opt.value)
  close()
}

function onButtonKey(e) {
  if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    if (!open.value) toggle()
    else if (e.key === 'Enter' && focusIndex.value >= 0) select(props.options[focusIndex.value])
  } else if (e.key === 'Escape') {
    if (open.value) { e.preventDefault(); close() }
  }
}

function onDocKey(e) {
  if (!open.value) return
  if (e.key === 'Escape') {
    e.preventDefault()
    close()
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusIndex.value = Math.min(focusIndex.value + 1, props.options.length - 1)
    scrollFocusedIntoView()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusIndex.value = Math.max(focusIndex.value - 1, 0)
    scrollFocusedIntoView()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (focusIndex.value >= 0) select(props.options[focusIndex.value])
  } else if (e.key === 'Home') {
    e.preventDefault()
    focusIndex.value = 0
    scrollFocusedIntoView()
  } else if (e.key === 'End') {
    e.preventDefault()
    focusIndex.value = props.options.length - 1
    scrollFocusedIntoView()
  }
}

function scrollFocusedIntoView() {
  nextTick(() => {
    const li = listEl.value?.children?.[focusIndex.value]
    li?.scrollIntoView?.({ block: 'nearest' })
  })
}

function onDocClick(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) close()
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onDocKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onDocKey)
})

watch(() => props.options, () => {
  if (focusIndex.value >= props.options.length) {
    focusIndex.value = Math.max(0, props.options.length - 1)
  }
})
</script>
