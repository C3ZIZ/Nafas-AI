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
    </header>

    <!-- Main -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Dashboard />
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
import Dashboard from './components/Dashboard.vue'
import { LOCALES, locale, setLocale, isRTL, t } from './i18n.js'
import { Stethoscope } from 'lucide-vue-next'
</script>
