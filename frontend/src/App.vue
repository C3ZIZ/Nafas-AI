<template>
  <div class="min-h-screen text-ink bg-surface-alt" :class="isRTL && 'ar'">
    <!-- Header -->
    <header class="sticky top-0 z-30 bg-surface-alt/85 backdrop-blur-md border-b border-line">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
        <!-- Brand -->
        <div class="flex items-center gap-3 min-w-0">
          <div class="h-9 w-9 rounded-xl bg-brand-600 grid place-items-center shrink-0">
            <Stethoscope class="h-5 w-5 text-white" :stroke-width="1.75" />
          </div>
          <div class="min-w-0 leading-tight">
            <h1 class="text-base sm:text-lg font-semibold tracking-tight truncate">{{ t('app_title') }}</h1>
            <p class="text-2xs sm:text-xs text-ink-muted truncate">{{ t('app_subtitle') }}</p>
          </div>
        </div>

        <!-- Right cluster -->
        <div class="flex items-center gap-2">
          <span class="hidden md:inline-flex pill pill-success">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            {{ t('api_live') }}
          </span>

          <!-- Locale toggle -->
          <div class="seg !p-0.5">
            <button
              v-for="(meta, key) in LOCALES"
              :key="key"
              @click="setLocale(key)"
              :class="['seg-btn !min-h-0 !py-1.5 !px-2.5 !text-xs', locale === key && 'seg-btn-active']"
              :aria-label="meta.label"
              :aria-pressed="locale === key">
              {{ meta.flag }}
            </button>
          </div>
        </div>
      </div>

      <!-- Top-level tabs -->
      <nav class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-center gap-1 -mb-px overflow-x-auto no-scrollbar">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :aria-current="activeTab === tab.key ? 'page' : undefined"
            :class="[
              'inline-flex items-center gap-2 px-3 sm:px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors',
              activeTab === tab.key
                ? 'border-brand-600 text-ink'
                : 'border-transparent text-ink-muted hover:text-ink hover:border-line-strong'
            ]">
            <component :is="tab.icon" class="h-4 w-4" :stroke-width="1.75" />
            {{ t(tab.labelKey) }}
          </button>
        </div>
      </nav>
    </header>

    <!-- Key-missing banner -->
    <div v-if="llmConfigured === false" class="bg-amber-50 border-b border-amber-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-2.5 flex items-start gap-2.5 text-xs sm:text-sm text-amber-900">
        <AlertTriangle class="h-4 w-4 mt-0.5 shrink-0" :stroke-width="2" />
        <div class="min-w-0">
          <span class="font-semibold">{{ t('no_key_title') }}.</span>
          <span class="text-amber-800"> {{ t('no_key_desc') }}</span>
        </div>
      </div>
    </div>

    <!-- Main -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Dashboard v-show="activeTab === 'triage'" />
      <DoctorChat v-if="activeTab === 'chat'" />
    </main>

    <!-- Footer -->
    <footer class="max-w-7xl mx-auto px-4 sm:px-6 py-8 mt-4">
      <div class="border-t border-line pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-2xs text-ink-subtle">
        <p>{{ t('footer') }}</p>
        <span class="md:hidden pill pill-success">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
          {{ t('api_live') }}
        </span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Dashboard from './components/Dashboard.vue'
import DoctorChat from './components/DoctorChat.vue'
import { LOCALES, locale, setLocale, isRTL, t } from './i18n.js'
import { Stethoscope, Activity, MessageSquareText, AlertTriangle } from 'lucide-vue-next'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const tabs = [
  { key: 'triage', labelKey: 'tab_triage', icon: Activity },
  { key: 'chat',   labelKey: 'tab_chat',   icon: MessageSquareText }
]
const activeTab = ref('triage')

// null = unknown, true = configured, false = HF_TOKEN missing
const llmConfigured = ref(null)

onMounted(async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/llm_status`)
    llmConfigured.value = !!data?.configured
  } catch {
    llmConfigured.value = null
  }
})
</script>
