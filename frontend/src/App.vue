<template>
  <div class="min-h-screen text-slate-900">
    <!-- Top nav -->
    <header class="sticky top-0 z-30 backdrop-blur-xl bg-white/70 border-b border-slate-200/70">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-accent-700 to-teal grid place-items-center shadow-glow">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-white" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 3v3m0 12v3m9-9h-3M6 12H3m13.5-6.5l-2 2m-9 9l-2 2m13 0l-2-2m-9-9l-2-2"/>
              <circle cx="12" cy="12" r="3.2"/>
            </svg>
          </div>
          <div class="min-w-0">
            <div class="flex items-baseline gap-2">
              <h1 class="text-lg sm:text-xl font-semibold tracking-tight truncate">Nafas&nbsp;AI</h1>
              <span class="text-xs text-slate-500 hidden sm:inline">نَفَس · Multi-modal Respiratory Triage</span>
            </div>
            <div class="text-[11px] text-slate-500 sm:hidden">Multi-modal Respiratory Triage</div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <span class="pill bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            API live
          </span>
          <a class="hidden sm:inline-flex pill bg-slate-100 text-slate-600 hover:bg-slate-200 transition" href="/docs" target="_blank">/docs</a>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Dashboard />
    </main>

    <footer class="max-w-7xl mx-auto px-4 sm:px-6 py-6 text-center text-xs text-slate-500">
      Educational decision-support · لا يُغني عن استشارة الطبيب
    </footer>
  </div>
</template>

<script setup>
import Dashboard from './components/Dashboard.vue'
</script>
