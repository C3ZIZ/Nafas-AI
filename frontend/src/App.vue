<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 class="text-2xl font-semibold">Nafas AI — Demo Dashboard</h1>
        <div class="text-sm text-slate-500">Demo: Multi-Modal Telemedicine</div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto p-6">
      <Dashboard />
    </main>
  </div>
</template>

<script setup>
import Dashboard from './components/Dashboard.vue'
</script>
