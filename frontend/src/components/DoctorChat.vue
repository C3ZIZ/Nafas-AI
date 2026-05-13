<template>
  <div class="space-y-5">
    <!-- Header -->
    <section class="card card-pad animate-fade-up">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-start gap-3 min-w-0">
          <div class="icon-tile shrink-0">
            <Bot class="h-5 w-5" :stroke-width="1.75" />
          </div>
          <div class="min-w-0">
            <h2 class="text-xl sm:text-2xl font-semibold tracking-tight">{{ t('chat_title') }}</h2>
            <p class="text-sm text-ink-muted mt-1 leading-relaxed">{{ t('chat_subtitle') }}</p>
          </div>
        </div>
        <button v-if="messages.length"
                @click="clearChat"
                class="btn-secondary btn-sm self-start sm:self-auto">
          <Trash2 class="h-3.5 w-3.5" :stroke-width="2" />
          {{ t('chat_clear') }}
        </button>
      </div>
    </section>

    <!-- Chat surface -->
    <section class="card flex flex-col h-[calc(100dvh-22rem)] min-h-[28rem] sm:min-h-[34rem] overflow-hidden">
      <!-- Messages -->
      <div ref="scrollerEl"
           class="flex-1 overflow-y-auto px-4 sm:px-6 py-5 space-y-5"
           role="log"
           aria-live="polite">
        <!-- Empty state -->
        <div v-if="!messages.length" class="h-full flex flex-col items-center justify-center text-center px-2">
          <div class="h-12 w-12 rounded-2xl bg-brand-50 text-brand-700 grid place-items-center">
            <MessageSquareText class="h-6 w-6" :stroke-width="1.5" />
          </div>
          <h3 class="mt-4 text-base font-semibold">{{ t('chat_empty_title') }}</h3>
          <p class="mt-1 text-sm text-ink-muted max-w-md leading-relaxed">{{ t('chat_empty_desc') }}</p>

          <div class="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-2 w-full max-w-3xl">
            <button v-for="key in exampleKeys" :key="key"
                    @click="sendExample(key)"
                    class="text-start rounded-xl border border-line bg-surface hover:border-brand-500 hover:shadow-soft transition-all duration-200 p-3 text-xs sm:text-sm text-ink-muted hover:text-ink leading-relaxed">
              <Sparkles class="h-3.5 w-3.5 text-brand-600 mb-1.5" :stroke-width="2" />
              {{ t(key) }}
            </button>
          </div>
        </div>

        <!-- Messages -->
        <template v-else>
          <div v-for="(m, i) in messages" :key="i"
               :class="['flex gap-2.5 sm:gap-3 animate-fade-up', m.role === 'user' && 'flex-row-reverse']">
            <div :class="[
              'h-8 w-8 rounded-xl grid place-items-center shrink-0',
              m.role === 'user' ? 'bg-stone-200 text-ink' : 'bg-brand-50 text-brand-700'
            ]">
              <component :is="m.role === 'user' ? User : Bot" class="h-4 w-4" :stroke-width="1.75" />
            </div>

            <div :class="['min-w-0 max-w-[85%] sm:max-w-[78%]', m.role === 'user' && 'text-end']">
              <div class="text-2xs text-ink-subtle mb-1 font-medium">
                {{ m.role === 'user' ? t('chat_you') : t('chat_assistant') }}
              </div>
              <div :class="[
                'rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed break-words',
                m.role === 'user'
                  ? 'bg-brand-600 text-white inline-block'
                  : m.error
                    ? 'bg-rose-50 border border-rose-200 text-rose-900'
                    : 'bg-surface-alt border border-line text-ink'
              ]">
                <div v-if="m.role === 'assistant'" v-html="renderMarkdown(m.content)"></div>
                <div v-else class="whitespace-pre-wrap">{{ m.content }}</div>
              </div>
            </div>
          </div>

          <!-- Pending -->
          <div v-if="pending" class="flex gap-3 animate-fade-up">
            <div class="h-8 w-8 rounded-xl grid place-items-center shrink-0 bg-brand-50 text-brand-700">
              <Bot class="h-4 w-4" :stroke-width="1.75" />
            </div>
            <div class="min-w-0">
              <div class="text-2xs text-ink-subtle mb-1 font-medium">{{ t('chat_assistant') }}</div>
              <div class="rounded-2xl px-3.5 py-2.5 bg-surface-alt border border-line inline-flex items-center gap-2 text-sm text-ink-muted">
                <Loader2 class="h-4 w-4 animate-spin text-brand-600" :stroke-width="2" />
                {{ t('chat_thinking') }}
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Composer -->
      <div class="border-t border-line bg-surface-alt p-3 sm:p-4">
        <div class="flex items-end gap-2">
          <textarea
            v-model="draft"
            ref="textareaEl"
            rows="1"
            :placeholder="t('chat_placeholder')"
            :disabled="pending"
            @keydown="onComposerKey"
            @input="autoGrow"
            class="field-input flex-1 resize-none max-h-40 leading-relaxed py-3"
            style="min-height: 48px;"></textarea>
          <button
            @click="send"
            :disabled="pending || !draft.trim()"
            class="btn-primary shrink-0 !px-3.5"
            :aria-label="t('chat_send')">
            <Send class="h-4 w-4" :stroke-width="2" />
            <span class="hidden sm:inline">{{ t('chat_send') }}</span>
          </button>
        </div>
        <p class="mt-2 text-2xs text-ink-subtle flex flex-wrap items-center justify-between gap-2">
          <span class="inline-flex items-center gap-1">
            <Info class="h-3 w-3" :stroke-width="2" />
            {{ t('chat_disclaimer') }}
          </span>
          <span class="hidden sm:inline">{{ t('chat_send_hint') }}</span>
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import axios from 'axios'
import { t, locale } from '../i18n.js'
import {
  Bot, User, Send, Trash2, Loader2, Info, Sparkles,
  MessageSquareText
} from 'lucide-vue-next'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const messages = ref([])      // { role: 'user'|'assistant', content, error? }
const draft = ref('')
const pending = ref(false)
const textareaEl = ref(null)
const scrollerEl = ref(null)

const exampleKeys = ['chat_example_1', 'chat_example_2', 'chat_example_3']

function autoGrow() {
  const el = textareaEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

function onComposerKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function sendExample(key) {
  draft.value = t(key)
  nextTick(() => { autoGrow(); send() })
}

function clearChat() {
  messages.value = []
  draft.value = ''
  nextTick(autoGrow)
}

async function send() {
  const text = draft.value.trim()
  if (!text || pending.value) return

  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  nextTick(autoGrow)
  pending.value = true
  scrollToBottom()

  try {
    const payload = {
      messages: messages.value
        .filter(m => !m.error)
        .map(m => ({ role: m.role, content: m.content })),
      temperature: 0.3,
      max_tokens: 768
    }
    const { data } = await axios.post(`${API_BASE}/doctor_chat`, payload)
    messages.value.push({ role: 'assistant', content: data.reply || '' })
  } catch (err) {
    const status = err?.response?.status
    const detail = err?.response?.data?.detail
    let msg
    if (status === 503) {
      msg = detail || t('chat_error_503')
    } else if (detail) {
      msg = detail
    } else {
      msg = t('chat_error_generic')
    }
    messages.value.push({ role: 'assistant', content: msg, error: true })
  } finally {
    pending.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    const el = scrollerEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(messages, scrollToBottom, { deep: true })

// Tiny, dependency-free markdown renderer: headings (#-###),
// bold/italic, inline code, code fences, unordered & ordered lists,
// links. Output is HTML-escaped first so model output cannot inject.
function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderMarkdown(src) {
  if (!src) return ''
  // Extract fenced code blocks first to protect them.
  const blocks = []
  let s = src.replace(/```([\s\S]*?)```/g, (_, code) => {
    blocks.push(code)
    return ` CODEBLOCK${blocks.length - 1} `
  })
  s = escapeHtml(s)

  // Inline code
  s = s.replace(/`([^`\n]+)`/g, '<code class="px-1 py-0.5 rounded bg-stone-100 text-ink text-[0.85em] font-mono">$1</code>')

  // Bold / italic
  s = s.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')

  // Links: [text](url)
  s = s.replace(/\[([^\]]+)\]\(((?:https?|mailto):[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener" class="text-brand-700 hover:text-brand-800 underline">$1</a>')

  // Headings (### / ## / #)
  s = s.replace(/^###\s+(.+)$/gm, '<h4 class="font-semibold text-ink mt-3 mb-1">$1</h4>')
  s = s.replace(/^##\s+(.+)$/gm, '<h3 class="font-semibold text-ink mt-3 mb-1.5">$1</h3>')
  s = s.replace(/^#\s+(.+)$/gm, '<h2 class="font-semibold text-ink text-base mt-3 mb-1.5">$1</h2>')

  // Lists — group consecutive lines starting with -/* or 1.
  const lines = s.split(/\n/)
  const out = []
  let ulOpen = false, olOpen = false
  for (const line of lines) {
    const ul = line.match(/^[-*]\s+(.+)$/)
    const ol = line.match(/^(\d+)\.\s+(.+)$/)
    if (ul) {
      if (olOpen) { out.push('</ol>'); olOpen = false }
      if (!ulOpen) { out.push('<ul class="list-disc ms-5 my-2 space-y-1">'); ulOpen = true }
      out.push(`<li>${ul[1]}</li>`)
    } else if (ol) {
      if (ulOpen) { out.push('</ul>'); ulOpen = false }
      if (!olOpen) { out.push('<ol class="list-decimal ms-5 my-2 space-y-1">'); olOpen = true }
      out.push(`<li>${ol[2]}</li>`)
    } else {
      if (ulOpen) { out.push('</ul>'); ulOpen = false }
      if (olOpen) { out.push('</ol>'); olOpen = false }
      if (line.trim() === '') {
        out.push('')
      } else if (/^<(h\d|ul|ol|li|pre)/.test(line)) {
        out.push(line)
      } else {
        out.push(`<p class="my-2">${line}</p>`)
      }
    }
  }
  if (ulOpen) out.push('</ul>')
  if (olOpen) out.push('</ol>')
  let html = out.join('\n')

  // Restore code blocks
  html = html.replace(/ CODEBLOCK(\d+) /g, (_, i) =>
    `<pre class="bg-stone-100 text-ink p-3 rounded-xl my-2 overflow-x-auto text-xs font-mono"><code>${escapeHtml(blocks[+i])}</code></pre>`
  )
  return html
}
</script>
