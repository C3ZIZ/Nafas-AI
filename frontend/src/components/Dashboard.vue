<template>
  <div class="space-y-6">
    <!-- Hero -->
    <section class="glass p-5 sm:p-6 bg-mesh-hero">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 class="text-xl sm:text-2xl font-semibold tracking-tight">{{ t('hero_title') }}</h2>
          <p class="text-sm text-slate-600 mt-1">{{ t('hero_desc') }}</p>
        </div>
        <div class="grid grid-cols-3 gap-3 md:max-w-md w-full">
          <div class="rounded-xl bg-white/70 border border-white/70 p-3 text-center">
            <div class="text-[11px] text-slate-500 uppercase tracking-wider">{{ t('pipeline_audio') }}</div>
            <div class="text-sm font-semibold text-slate-900 mt-0.5">CNN</div>
          </div>
          <div class="rounded-xl bg-white/70 border border-white/70 p-3 text-center">
            <div class="text-[11px] text-slate-500 uppercase tracking-wider">{{ t('pipeline_vitals') }}</div>
            <div class="text-sm font-semibold text-slate-900 mt-0.5">RandomForest</div>
          </div>
          <div class="rounded-xl bg-white/70 border border-white/70 p-3 text-center">
            <div class="text-[11px] text-slate-500 uppercase tracking-wider">{{ t('pipeline_symptoms') }}</div>
            <div class="text-sm font-semibold text-slate-900 mt-0.5">NLP</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Main grid -->
    <div class="grid gap-6 grid-cols-1 lg:grid-cols-12">
      <!-- Patient profile -->
      <section class="glass p-5 sm:p-6 lg:col-span-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold">{{ t('patient_profile') }}</h3>
          <span class="pill bg-slate-100 text-slate-600">{{ t('step') }} 1</span>
        </div>

        <div class="space-y-3.5">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label">{{ t('age') }}</label>
              <input v-model.number="profile.age" type="number" min="0" step="0.1" class="field-input" />
            </div>
            <div>
              <label class="field-label">{{ t('sex') }}</label>
              <select v-model.number="profile.sex" class="field-input">
                <option :value="1">{{ t('male') }}</option>
                <option :value="0">{{ t('female') }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label">{{ t('bmi') }}</label>
              <input v-model.number="profile.bmi" type="number" step="0.1" class="field-input" />
            </div>
            <div>
              <label class="field-label">{{ t('spo2') }}</label>
              <input v-model.number="profile.spo2" type="number" step="0.1" class="field-input" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label">{{ t('temperature') }}</label>
              <input v-model.number="profile.temperature" type="number" step="0.1" class="field-input" />
            </div>
            <div>
              <label class="field-label">{{ t('smoker') }}</label>
              <select v-model.number="profile.smoker" class="field-input">
                <option :value="0">{{ t('no') }}</option>
                <option :value="1">{{ t('yes') }}</option>
              </select>
            </div>
          </div>

          <div>
            <label class="field-label">{{ t('patient_notes') }}</label>
            <textarea
              v-model="profile.patient_notes"
              rows="4"
              :placeholder="t('patient_notes_placeholder')"
              class="field-input resize-y"
            ></textarea>
          </div>
        </div>
      </section>

      <!-- Audio source -->
      <section class="glass p-5 sm:p-6 lg:col-span-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold">{{ t('audio_source') }}</h3>
          <span class="pill bg-slate-100 text-slate-600">{{ t('step') }} 2</span>
        </div>

        <div class="flex bg-slate-100/80 rounded-xl p-1 mb-4">
          <button class="seg-btn" :class="tab === 'sample' && 'seg-btn-active'" @click="setTab('sample')">{{ t('tab_sample') }}</button>
          <button class="seg-btn" :class="tab === 'upload' && 'seg-btn-active'" @click="setTab('upload')">{{ t('tab_upload') }}</button>
          <button class="seg-btn" :class="tab === 'record' && 'seg-btn-active'" @click="setTab('record')">{{ t('tab_record') }}</button>
        </div>

        <div v-if="tab === 'sample'" class="space-y-3">
          <label class="field-label">{{ t('choose_sample') }}</label>
          <select v-model="selectedSample" class="field-input">
            <option disabled value="">{{ t('select_placeholder') }}</option>
            <option v-for="s in sampleFiles" :key="s.filename" :value="s.filename">
              {{ s.label }} · {{ s.filename }}
            </option>
          </select>
          <p class="text-xs text-slate-500">{{ t('samples_hint') }}</p>
          <div v-if="selectedSample" class="pt-1">
            <audio v-if="serverAudioUrl" :src="serverAudioUrl" controls class="w-full"></audio>
          </div>
        </div>

        <div v-if="tab === 'upload'" class="space-y-3">
          <label
            class="block border-2 border-dashed border-slate-300 hover:border-accent transition rounded-xl p-6 text-center cursor-pointer bg-white/50"
            @dragover.prevent
            @drop.prevent="onDrop"
          >
            <input type="file" accept="audio/*" class="hidden" @change="onFileSelected" ref="fileInput" />
            <div class="flex flex-col items-center gap-2">
              <svg class="h-8 w-8 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0l-4 4m4-4l4 4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/>
              </svg>
              <div class="text-sm text-slate-600">
                <button type="button" class="font-medium text-accent-700 hover:text-accent" @click="$refs.fileInput.click()">{{ t('click_to_upload') }}</button>
                {{ t('or_drag_drop') }}
              </div>
              <div class="text-xs text-slate-400">{{ t('file_types') }}</div>
            </div>
          </label>
          <div v-if="localAudioUrl" class="pt-1 space-y-2">
            <div class="text-xs text-slate-500 truncate">{{ selectedFile?.name }}</div>
            <audio :src="localAudioUrl" controls class="w-full"></audio>
          </div>
        </div>

        <div v-if="tab === 'record'" class="space-y-3">
          <div class="rounded-xl border border-slate-200 bg-white/60 p-4 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <span v-if="isRecording" class="h-2.5 w-2.5 rounded-full bg-red-500 rec-dot"></span>
              <span v-else class="h-2.5 w-2.5 rounded-full bg-slate-300"></span>
              <div class="text-sm">
                <div class="font-medium text-slate-800">{{ isRecording ? t('recording') : t('mic_idle') }}</div>
                <div class="text-xs text-slate-500">{{ t('mic_hint') }}</div>
              </div>
            </div>
            <button @click="toggleRecording" :class="isRecording ? 'btn bg-red-500 text-white hover:bg-red-600' : 'btn-primary'">
              {{ isRecording ? t('stop') : t('start') }}
            </button>
          </div>
          <div v-if="recordedUrl" class="pt-1">
            <audio :src="recordedUrl" controls class="w-full"></audio>
          </div>
        </div>

        <div class="mt-5">
          <button @click="runDiagnosisFromSelected" :disabled="loading || !canRun" class="btn-primary w-full text-base">
            <span v-if="loading" class="spinner"></span>
            <svg v-else viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
            </svg>
            <span>{{ loading ? t('running') : t('run_diagnosis') }}</span>
          </button>
          <p v-if="!canRun" class="text-xs text-slate-500 mt-2 text-center">{{ t('pick_first') }}</p>
        </div>
      </section>

      <!-- Result snapshot -->
      <section class="glass p-5 sm:p-6 lg:col-span-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold">{{ t('diagnosis') }}</h3>
          <span class="pill bg-slate-100 text-slate-600">{{ t('step') }} 3</span>
        </div>

        <div v-if="!result && !loading" class="text-center py-10">
          <div class="mx-auto h-14 w-14 rounded-full bg-slate-100 grid place-items-center">
            <svg class="h-7 w-7 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-3-3v6m9 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <p class="mt-3 text-sm text-slate-500">{{ t('empty_diagnosis') }}</p>
        </div>

        <div v-else-if="loading" class="space-y-3">
          <div class="skeleton h-24"></div>
          <div class="skeleton h-4 w-3/4"></div>
          <div class="skeleton h-4 w-2/3"></div>
          <div class="skeleton h-4 w-1/2"></div>
        </div>

        <div v-else class="space-y-5">
          <div class="rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 text-white p-5 relative overflow-hidden">
            <div class="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-accent/30 blur-2xl"></div>
            <div class="relative flex items-center justify-between">
              <div class="min-w-0">
                <div class="text-[11px] uppercase tracking-wider text-white/60">{{ t('most_likely') }}</div>
                <h4 class="text-2xl font-bold mt-1 truncate">{{ localizedDiseaseName }}</h4>
                <div class="text-sm text-white/70 mt-0.5">{{ t('fused_confidence') }} {{ result.overall_confidence }}</div>
                <div v-if="result.medication_suggestions?.icd10" class="text-[11px] text-white/50 mt-1">{{ t('icd10') }}: {{ result.medication_suggestions.icd10 }}</div>
              </div>
              <div class="w-20 h-20 shrink-0">
                <svg viewBox="0 0 36 36" class="w-20 h-20">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="3.5" />
                  <path :d="progressArc" fill="none" stroke="#22d3ee" stroke-width="3.5" stroke-linecap="round" />
                  <text x="18" y="20.5" text-anchor="middle" font-size="7" fill="#fff" font-weight="700">{{ numericConfidence }}%</text>
                </svg>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <div class="rounded-xl bg-white/70 border border-slate-200 p-3 text-center">
              <div class="text-[10px] uppercase tracking-wider text-slate-500">{{ t('audio_cnn') }}</div>
              <div class="text-xs font-semibold text-slate-900 mt-1 truncate">{{ result.model_breakdown?.audio_cnn_prediction }}</div>
            </div>
            <div class="rounded-xl bg-white/70 border border-slate-200 p-3 text-center">
              <div class="text-[10px] uppercase tracking-wider text-slate-500">{{ t('vitals_rf') }}</div>
              <div class="text-xs font-semibold text-slate-900 mt-1 truncate">{{ result.model_breakdown?.vitals_rf_prediction }}</div>
            </div>
            <div class="rounded-xl bg-white/70 border border-slate-200 p-3 text-center">
              <div class="text-[10px] uppercase tracking-wider text-slate-500">{{ t('symptoms_nlp') }}</div>
              <div class="text-xs font-semibold text-slate-900 mt-1 truncate">{{ result.model_breakdown?.symptoms_nlp_prediction }}</div>
            </div>
          </div>

          <div v-if="result.all_disease_probabilities">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-semibold">{{ t('class_probabilities') }}</h4>
              <button class="text-xs text-accent-700 hover:underline" @click="showAllProbs = !showAllProbs">
                {{ showAllProbs ? t('show_top_4') : t('show_all') }}
              </button>
            </div>
            <div class="space-y-2">
              <div v-for="row in visibleProbs" :key="row.name" class="text-xs">
                <div class="flex justify-between">
                  <div class="font-medium text-slate-700">{{ row.name }}</div>
                  <div class="text-slate-500">{{ row.value }}%</div>
                </div>
                <div class="w-full bg-slate-100 h-2 rounded mt-1 overflow-hidden">
                  <div class="bar-fill h-2 rounded bg-gradient-to-r from-accent-700 to-teal"
                       :style="{ '--w': row.value + '%', width: row.value + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Doctor summary + treatment goals + red flags -->
    <div v-if="result" class="grid gap-6 grid-cols-1 lg:grid-cols-12">
      <section class="glass p-5 sm:p-6 lg:col-span-5">
        <div class="flex items-center gap-2 mb-3">
          <div class="h-8 w-8 rounded-lg bg-accent/15 text-accent-700 grid place-items-center">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-3-3v6m-7 4h16a2 2 0 002-2V6a2 2 0 00-2-2H4a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          </div>
          <h3 class="text-base font-semibold">{{ t('doctors_summary') }}</h3>
        </div>
        <p class="text-sm text-slate-700 leading-relaxed">{{ overviewText }}</p>

        <h4 class="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500">{{ t('recommended_precautions') }}</h4>
        <ul class="mt-2 space-y-1.5">
          <li v-for="(p, i) in result.doctor_summary?.recommended_precautions || []" :key="'p'+i"
              class="text-sm text-slate-700 flex items-start gap-2">
            <span class="mt-1 h-1.5 w-1.5 rounded-full bg-accent shrink-0"></span>
            <span>{{ p }}</span>
          </li>
        </ul>

        <div v-if="treatmentGoals.length" class="mt-4">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-500">{{ t('treatment_goals') }}</h4>
          <ul class="mt-2 space-y-1.5">
            <li v-for="(g, i) in treatmentGoals" :key="'g'+i" class="text-sm text-slate-700 flex items-start gap-2">
              <span class="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0"></span>
              <span>{{ g }}</span>
            </li>
          </ul>
        </div>

        <div v-if="redFlags.length" class="mt-4 rounded-xl bg-rose-50 border border-rose-200 p-3">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-rose-700">{{ t('red_flags') }}</h4>
          <ul class="mt-2 space-y-1.5">
            <li v-for="(f, i) in redFlags" :key="'rf'+i" class="text-sm text-rose-800 flex items-start gap-2">
              <span class="mt-1 h-1.5 w-1.5 rounded-full bg-rose-500 shrink-0"></span>
              <span>{{ f }}</span>
            </li>
          </ul>
        </div>
      </section>

      <!-- Saudi medications -->
      <section class="glass p-5 sm:p-6 lg:col-span-7">
        <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div class="flex items-center gap-2">
            <div class="h-8 w-8 rounded-lg bg-emerald-100 text-emerald-700 grid place-items-center">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2m14 0V7a2 2 0 00-2-2H7a2 2 0 00-2 2v4m7-2v4"/></svg>
            </div>
            <div>
              <h3 class="text-base font-semibold">{{ t('pharmacy_suggestions') }}</h3>
              <p class="text-[11px] text-slate-500">{{ t('available_at') }}</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-1.5">
            <button v-for="p in pharmacyFilters" :key="p"
              @click="togglePharmacy(p)"
              :class="activePharmacies.includes(p) ? 'pill bg-accent text-white' : 'pill bg-slate-100 text-slate-600 hover:bg-slate-200'">
              {{ pharmacyLabel(p) }}
            </button>
          </div>
        </div>

        <!-- Classification legend -->
        <div v-if="legendList.length" class="flex flex-wrap gap-1.5 mb-4">
          <span v-for="l in legendList" :key="l.key"
            :class="['pill border', classBadge(l.color, true)]">
            {{ isRTL ? l.ar : l.en }}
          </span>
        </div>

        <div v-if="filteredMeds.length === 0" class="text-sm text-slate-500 py-6 text-center">
          {{ t('no_meds') }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <article v-for="(m, i) in filteredMeds" :key="i"
            class="rounded-xl border border-slate-200 bg-white/80 p-4 hover:shadow-soft transition">
            <!-- Header -->
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="font-semibold text-slate-900 truncate">{{ isRTL ? m.brand_ar : m.brand }}</div>
                <div class="text-xs text-slate-500">{{ isRTL ? (m.generic_ar || m.generic) : m.generic }}</div>
                <div v-if="!isRTL" class="ar text-sm text-slate-700 mt-1" dir="rtl">{{ m.brand_ar }}</div>
                <div v-else class="text-xs text-slate-500 mt-1" dir="ltr">{{ m.brand }}</div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-bold text-emerald-700">{{ m.indicative_price_sar }} <span class="text-[10px] font-medium text-slate-500">SAR</span></div>
                <span :class="m.rx_required ? 'pill bg-amber-50 text-amber-700 border border-amber-200' : 'pill bg-emerald-50 text-emerald-700 border border-emerald-200'">
                  {{ m.rx_required ? t('rx') : t('otc') }}
                </span>
              </div>
            </div>

            <!-- Classification + evidence -->
            <div class="flex flex-wrap items-center gap-1.5 mt-3">
              <span v-if="legendFor(m.classification)"
                class="pill border"
                :class="classBadge(legendFor(m.classification).color)">
                {{ isRTL ? legendFor(m.classification).ar : legendFor(m.classification).en }}
              </span>
              <span v-if="m.evidence_level" class="pill bg-slate-100 text-slate-600 border border-slate-200">
                {{ t('evidence_level') }}: {{ m.evidence_level }}
              </span>
              <span v-if="m.age_group" class="pill bg-slate-100 text-slate-600 border border-slate-200">
                {{ t('age_group') }}: {{ ageLabel(m.age_group) }}
              </span>
              <span v-if="m.category" class="pill bg-slate-50 text-slate-500 border border-slate-200">
                {{ m.category }}
              </span>
            </div>

            <!-- Mechanism / dosage / side effects toggle -->
            <div class="mt-3">
              <button class="text-xs text-accent-700 hover:underline" @click="toggleExpand(i)">
                {{ expanded[i] ? t('collapse') : t('expand') }}
              </button>
            </div>

            <div v-if="expanded[i]" class="mt-2 space-y-2 text-xs">
              <div>
                <div class="text-[10px] uppercase tracking-wider text-slate-400">{{ t('mechanism') }}</div>
                <p class="text-slate-700">{{ isRTL ? m.mechanism_ar : m.mechanism_en }}</p>
              </div>
              <div>
                <div class="text-[10px] uppercase tracking-wider text-slate-400">{{ t('dosage') }}</div>
                <p class="text-slate-700">{{ isRTL ? m.dosage_hint_ar : m.dosage_hint_en }}</p>
              </div>
              <div>
                <div class="text-[10px] uppercase tracking-wider text-slate-400">{{ t('side_effects') }}</div>
                <p class="text-slate-700">{{ isRTL ? m.side_effects_ar : m.side_effects_en }}</p>
              </div>
              <div>
                <div class="text-[10px] uppercase tracking-wider text-slate-400">{{ t('contraindications') }}</div>
                <p class="text-slate-700">{{ isRTL ? m.contraindications_ar : m.contraindications_en }}</p>
              </div>
              <div v-if="m.sources_resolved && m.sources_resolved.length">
                <div class="text-[10px] uppercase tracking-wider text-slate-400">{{ t('sources') }}</div>
                <ul class="mt-1 space-y-0.5">
                  <li v-for="src in m.sources_resolved" :key="src.id">
                    <a :href="src.url" target="_blank" rel="noopener"
                       class="text-accent-700 hover:underline">
                      {{ isRTL ? src.name_ar : src.name_en }}
                    </a>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Footer: pharmacies -->
            <div class="flex items-center justify-end gap-1 mt-3 pt-3 border-t border-slate-100 flex-wrap">
              <span v-for="ph in m.pharmacies" :key="ph" class="pill bg-slate-100 text-slate-600 text-[10px]">{{ pharmacyLabel(ph) }}</span>
            </div>
          </article>
        </div>

        <div v-if="result.medication_suggestions" class="mt-4 rounded-xl bg-amber-50/70 border border-amber-200 px-3 py-2.5 text-xs text-amber-800">
          <div v-if="!isRTL">{{ result.medication_suggestions.disclaimer_en }}</div>
          <div v-else dir="rtl" class="ar">{{ result.medication_suggestions.disclaimer_ar }}</div>
        </div>
      </section>
    </div>

    <!-- Data sources panel -->
    <section v-if="result && primarySources.length" class="glass p-5 sm:p-6">
      <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div>
          <h3 class="text-base font-semibold">{{ t('data_sources_title') }}</h3>
          <p class="text-xs text-slate-500 mt-0.5">{{ t('data_sources_desc') }}</p>
        </div>
        <button class="text-xs text-accent-700 hover:underline" @click="showSources = !showSources">
          {{ showSources ? t('collapse') : t('expand') }}
        </button>
      </div>
      <div v-if="showSources" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <a v-for="src in primarySources" :key="src.id" :href="src.url" target="_blank" rel="noopener"
           class="rounded-xl border border-slate-200 bg-white/80 p-3 hover:bg-white hover:border-accent transition block">
          <div class="text-[10px] uppercase tracking-wider text-slate-400">{{ src.type }}</div>
          <div class="text-sm font-semibold text-slate-900 mt-1">{{ isRTL ? src.name_ar : src.name_en }}</div>
          <div class="text-[11px] text-accent-700 truncate mt-1">{{ src.url }}</div>
        </a>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import axios from 'axios'
import { t, locale, isRTL } from '../i18n.js'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const axiosInstance = axios.create({ baseURL: API_BASE })

const profile = ref({
  age: 35,
  sex: 1,
  bmi: 25.0,
  spo2: 98.0,
  temperature: 36.6,
  smoker: 0,
  patient_notes: 'Productive cough for 3 days, mild chest tightness in the evenings.'
})

const tab = ref('sample')
const sampleFiles = ref([
  { label: 'Healthy', filename: '102_1b1_Ar_sc_Meditron.wav' },
  { label: 'COPD', filename: '104_1b1_Al_sc_Litt3200.wav' },
  { label: 'Asthma', filename: '103_2b2_Ar_mc_LittC2SE.wav' },
  { label: 'Bronchiectasis', filename: '111_1b2_Tc_sc_Meditron.wav' },
  { label: 'Pneumonia', filename: '122_2b1_Al_mc_LittC2SE.wav' },
  { label: 'URTI', filename: '101_1b1_Al_sc_Meditron.wav' },
  { label: 'LRTI', filename: '108_1b1_Al_sc_Meditron.wav' },
  { label: 'Bronchiolitis', filename: '149_1b1_Al_sc_Meditron.wav' }
])

const selectedSample = ref('')
const selectedFile = ref(null)
const localAudioUrl = ref('')

let mediaRecorder = null
let currentStream = null
const isRecording = ref(false)
const recordedBlob = ref(null)
const recordedUrl = ref('')

const loading = ref(false)
const result = ref(null)
const showAllProbs = ref(false)
const showSources = ref(true)
const expanded = reactive({})

const pharmacyFilters = ['Nahdi', 'Al-Dawaa', 'Al-Mamlaka']
const activePharmacies = ref([...pharmacyFilters])

const PHARMACY_AR = { 'Nahdi': 'النهدي', 'Al-Dawaa': 'الدواء', 'Al-Mamlaka': 'المملكة' }
function pharmacyLabel(p) { return isRTL.value ? (PHARMACY_AR[p] || p) : p }
function ageLabel(g) {
  if (g === 'adult') return t('age_adult')
  if (g === 'pediatric') return t('age_pediatric')
  return t('age_all')
}

const serverAudioUrl = computed(() =>
  selectedSample.value ? `${API_BASE}/audio/${encodeURIComponent(selectedSample.value)}` : null
)

const canRun = computed(() => {
  if (tab.value === 'sample') return !!selectedSample.value
  if (tab.value === 'upload') return !!selectedFile.value
  if (tab.value === 'record') return !!recordedBlob.value
  return false
})

const sortedProbs = computed(() => {
  const obj = result.value?.all_disease_probabilities
  if (!obj) return []
  return Object.entries(obj)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})
const visibleProbs = computed(() => showAllProbs.value ? sortedProbs.value : sortedProbs.value.slice(0, 4))

const filteredMeds = computed(() => {
  const items = result.value?.medication_suggestions?.items || []
  if (activePharmacies.value.length === 0) return items
  return items.filter(m => (m.pharmacies || []).some(p => activePharmacies.value.includes(p)))
})

const localizedDiseaseName = computed(() => {
  if (!result.value) return ''
  const ms = result.value.medication_suggestions
  if (isRTL.value && ms?.disease_ar) return ms.disease_ar
  return result.value.final_diagnosis
})

const overviewText = computed(() => {
  const ms = result.value?.medication_suggestions
  if (isRTL.value && ms?.overview_ar) return ms.overview_ar
  if (ms?.overview_en) return ms.overview_en
  return result.value?.doctor_summary?.disease_description || ''
})

const treatmentGoals = computed(() => {
  const ms = result.value?.medication_suggestions
  if (!ms) return []
  return isRTL.value ? (ms.treatment_goals_ar || []) : (ms.treatment_goals_en || [])
})

const redFlags = computed(() => {
  const ms = result.value?.medication_suggestions
  if (!ms) return []
  return isRTL.value ? (ms.red_flags_ar || []) : (ms.red_flags_en || [])
})

const primarySources = computed(() => result.value?.medication_suggestions?.primary_sources || [])

const legendList = computed(() => {
  const legend = result.value?.medication_suggestions?.classification_legend || {}
  const present = new Set((result.value?.medication_suggestions?.items || []).map(m => m.classification))
  return Object.entries(legend)
    .filter(([k]) => present.has(k))
    .sort((a, b) => (a[1].rank || 99) - (b[1].rank || 99))
    .map(([key, v]) => ({ key, ...v }))
})
function legendFor(key) {
  const legend = result.value?.medication_suggestions?.classification_legend || {}
  return key && legend[key] ? legend[key] : null
}

function classBadge(color, faded = false) {
  const base = {
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    indigo:  'bg-indigo-50 text-indigo-700 border-indigo-200',
    rose:    'bg-rose-50 text-rose-700 border-rose-200',
    blue:    'bg-blue-50 text-blue-700 border-blue-200',
    violet:  'bg-violet-50 text-violet-700 border-violet-200',
    amber:   'bg-amber-50 text-amber-700 border-amber-200',
    slate:   'bg-slate-50 text-slate-600 border-slate-200',
    teal:    'bg-teal-50 text-teal-700 border-teal-200'
  }
  return base[color] || base.slate
}

function setTab(name) { tab.value = name }
function togglePharmacy(p) {
  if (activePharmacies.value.includes(p)) activePharmacies.value = activePharmacies.value.filter(x => x !== p)
  else activePharmacies.value = [...activePharmacies.value, p]
}
function toggleExpand(i) { expanded[i] = !expanded[i] }

function onFileSelected(e) {
  const f = e.target.files?.[0]
  if (!f) return
  selectedFile.value = f
  if (localAudioUrl.value) URL.revokeObjectURL(localAudioUrl.value)
  localAudioUrl.value = URL.createObjectURL(f)
}
function onDrop(e) {
  const f = e.dataTransfer?.files?.[0]
  if (!f) return
  selectedFile.value = f
  if (localAudioUrl.value) URL.revokeObjectURL(localAudioUrl.value)
  localAudioUrl.value = URL.createObjectURL(f)
}

async function uploadFile(file) {
  const fd = new FormData()
  fd.append('file', file)
  const resp = await axiosInstance.post('/upload_audio/', fd)
  return resp.data.filename
}

function toggleRecording() {
  if (isRecording.value) mediaRecorder?.stop()
  else startRecording()
}

async function startRecording() {
  try {
    currentStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(currentStream)
    const chunks = []
    mediaRecorder.ondataavailable = (ev) => chunks.push(ev.data)
    mediaRecorder.onstop = () => {
      recordedBlob.value = new Blob(chunks, { type: 'audio/wav' })
      if (recordedUrl.value) URL.revokeObjectURL(recordedUrl.value)
      recordedUrl.value = URL.createObjectURL(recordedBlob.value)
      isRecording.value = false
      if (currentStream) { currentStream.getTracks().forEach((t) => t.stop()); currentStream = null }
    }
    mediaRecorder.start()
    isRecording.value = true
  } catch (err) {
    alert('Cannot access microphone: ' + err)
  }
}

async function runDiagnosisFromSelected() {
  if (!canRun.value) return
  if (tab.value === 'sample') return runWithSample()
  if (tab.value === 'upload') return uploadAndDiagnose(selectedFile.value)
  if (tab.value === 'record') return uploadAndDiagnose(new File([recordedBlob.value], 'recording.wav', { type: 'audio/wav' }))
}

async function runWithSample() {
  loading.value = true
  try { await runDiagnosis(selectedSample.value) }
  catch (err) { alert('Diagnosis failed: ' + (err.response?.data?.detail || err.message)) }
  finally { loading.value = false }
}

async function uploadAndDiagnose(file) {
  loading.value = true
  try {
    const filename = await uploadFile(file)
    await runDiagnosis(filename)
  } catch (err) {
    alert('Upload failed: ' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

async function runDiagnosis(filename) {
  loading.value = true
  result.value = null
  try {
    const payload = {
      age: Number(profile.value.age),
      sex: Number(profile.value.sex),
      bmi: Number(profile.value.bmi),
      spo2: Number(profile.value.spo2),
      temperature: Number(profile.value.temperature),
      smoker: Number(profile.value.smoker),
      patient_notes: String(profile.value.patient_notes || '')
    }
    const resp = await axiosInstance.post(`/diagnose_trinity/${encodeURIComponent(filename)}`, payload)
    result.value = resp.data
    Object.keys(expanded).forEach(k => delete expanded[k])
  } catch (err) {
    console.error(err)
    alert('API error: ' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const numericConfidence = computed(() => {
  if (!result.value || !result.value.overall_confidence) return 0
  const v = parseFloat(String(result.value.overall_confidence).replace('%', ''))
  return Number.isFinite(v) ? Math.round(v) : 0
})

const progressArc = computed(() => {
  const pct = Math.max(0, Math.min(100, numericConfidence.value))
  if (pct <= 0) return 'M 18 2.0845'
  const angle = (pct / 100) * 359.999
  const large = angle > 180 ? 1 : 0
  const radius = 15.9155
  const start = polarToCartesian(18, 18, radius, 0)
  const end = polarToCartesian(18, 18, radius, angle)
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${large} 1 ${end.x} ${end.y}`
})

function polarToCartesian(cx, cy, r, angleDeg) {
  const angleRad = (angleDeg - 90) * Math.PI / 180.0
  return { x: cx + (r * Math.cos(angleRad)), y: cy + (r * Math.sin(angleRad)) }
}
</script>
