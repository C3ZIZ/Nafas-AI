<template>
  <div class="space-y-5 sm:space-y-6">
    <!-- Hero -->
    <section class="card card-pad animate-fade-up">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
        <div class="max-w-2xl">
          <span class="pill pill-brand mb-3">
            <Sparkles class="h-3 w-3" :stroke-width="2" />
            {{ t('ai_model_label') }}
          </span>
          <h2 class="text-2xl sm:text-3xl font-semibold tracking-tight text-ink">{{ t('hero_title') }}</h2>
          <p class="text-sm sm:text-base text-ink-muted mt-2 leading-relaxed">{{ t('hero_desc') }}</p>
        </div>

        <div class="grid grid-cols-3 gap-2 sm:gap-3 lg:max-w-md w-full">
          <div v-for="m in modelChips" :key="m.label"
               class="rounded-xl border border-line bg-surface-alt p-3 flex flex-col items-center gap-1.5 text-center">
            <component :is="m.icon" class="h-4 w-4 text-brand-600" :stroke-width="1.75" />
            <div class="text-2xs text-ink-muted uppercase tracking-wider">{{ m.label }}</div>
            <div class="text-2xs sm:text-xs font-semibold text-ink">{{ m.model }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Main 3-col grid -->
    <div class="grid gap-5 sm:gap-6 grid-cols-1 lg:grid-cols-12">
      <!-- STEP 1 · Patient profile -->
      <section class="card card-pad lg:col-span-4">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-3 min-w-0">
            <div class="icon-tile"><User class="h-5 w-5" :stroke-width="1.75" /></div>
            <div class="min-w-0">
              <h3 class="section-title truncate">{{ t('patient_profile') }}</h3>
              <p class="section-sub">{{ t('step') }} 1</p>
            </div>
          </div>
          <span class="step-badge">01</span>
        </div>

        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label">{{ t('age') }}</label>
              <input v-model.number="profile.age" type="number" min="0" step="0.1" class="field-input tabular" />
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
              <input v-model.number="profile.bmi" type="number" step="0.1" class="field-input tabular" />
            </div>
            <div>
              <label class="field-label">{{ t('spo2') }}</label>
              <input v-model.number="profile.spo2" type="number" step="0.1" class="field-input tabular" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="field-label">{{ t('temperature') }}</label>
              <input v-model.number="profile.temperature" type="number" step="0.1" class="field-input tabular" />
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
              class="field-input resize-y leading-relaxed"
            ></textarea>
          </div>
        </div>
      </section>

      <!-- STEP 2 · Audio source -->
      <section class="card card-pad lg:col-span-4">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-3 min-w-0">
            <div class="icon-tile"><AudioLines class="h-5 w-5" :stroke-width="1.75" /></div>
            <div class="min-w-0">
              <h3 class="section-title truncate">{{ t('audio_source') }}</h3>
              <p class="section-sub">{{ t('step') }} 2</p>
            </div>
          </div>
          <span class="step-badge">02</span>
        </div>

        <div class="seg mb-4">
          <button class="seg-btn" :class="tab === 'sample' && 'seg-btn-active'" @click="setTab('sample')" :aria-pressed="tab === 'sample'">
            <FileAudio class="h-3.5 w-3.5" :stroke-width="1.75" /> {{ t('tab_sample') }}
          </button>
          <button class="seg-btn" :class="tab === 'upload' && 'seg-btn-active'" @click="setTab('upload')" :aria-pressed="tab === 'upload'">
            <Upload class="h-3.5 w-3.5" :stroke-width="1.75" /> {{ t('tab_upload') }}
          </button>
          <button class="seg-btn" :class="tab === 'record' && 'seg-btn-active'" @click="setTab('record')" :aria-pressed="tab === 'record'">
            <Mic class="h-3.5 w-3.5" :stroke-width="1.75" /> {{ t('tab_record') }}
          </button>
        </div>

        <!-- Sample -->
        <div v-if="tab === 'sample'" class="space-y-3">
          <label class="field-label">{{ t('choose_sample') }}</label>
          <select v-model="selectedSample" class="field-input">
            <option disabled value="">{{ t('select_placeholder') }}</option>
            <option v-for="s in sampleFiles" :key="s.filename" :value="s.filename">
              {{ s.label }} · {{ s.filename }}
            </option>
          </select>
          <p class="text-2xs text-ink-subtle">{{ t('samples_hint') }}</p>
          <div v-if="selectedSample" class="pt-1">
            <audio v-if="serverAudioUrl" :src="serverAudioUrl" controls></audio>
          </div>
        </div>

        <!-- Upload -->
        <div v-if="tab === 'upload'" class="space-y-3">
          <label
            class="block border-2 border-dashed border-line-strong hover:border-brand-500 transition-colors rounded-2xl p-6 text-center cursor-pointer bg-surface-alt"
            @dragover.prevent
            @drop.prevent="onDrop"
          >
            <input type="file" accept="audio/*" class="hidden" @change="onFileSelected" ref="fileInput" />
            <div class="flex flex-col items-center gap-2">
              <div class="h-10 w-10 rounded-xl bg-brand-50 text-brand-700 grid place-items-center">
                <UploadCloud class="h-5 w-5" :stroke-width="1.75" />
              </div>
              <div class="text-sm text-ink-muted">
                <button type="button" class="font-medium text-brand-700 hover:text-brand-800" @click="$refs.fileInput.click()">{{ t('click_to_upload') }}</button>
                <span> {{ t('or_drag_drop') }}</span>
              </div>
              <div class="text-2xs text-ink-subtle">{{ t('file_types') }}</div>
            </div>
          </label>
          <div v-if="localAudioUrl" class="pt-1 space-y-2">
            <div class="text-2xs text-ink-muted truncate flex items-center gap-1.5">
              <FileAudio class="h-3.5 w-3.5 shrink-0" :stroke-width="1.75" />
              {{ selectedFile?.name }}
            </div>
            <audio :src="localAudioUrl" controls></audio>
          </div>
        </div>

        <!-- Record -->
        <div v-if="tab === 'record'" class="space-y-3">
          <div class="rounded-2xl border border-line bg-surface-alt p-4 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
              <div class="relative shrink-0">
                <div :class="isRecording ? 'bg-rose-100 text-rose-600' : 'bg-stone-100 text-ink-muted'"
                     class="h-10 w-10 rounded-xl grid place-items-center">
                  <Mic class="h-4 w-4" :stroke-width="2" />
                </div>
                <span v-if="isRecording" class="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-rose-500 rec-dot ring-2 ring-surface"></span>
              </div>
              <div class="text-sm min-w-0">
                <div class="font-medium text-ink truncate">{{ isRecording ? t('recording') : t('mic_idle') }}</div>
                <div class="text-2xs text-ink-subtle truncate">{{ t('mic_hint') }}</div>
              </div>
            </div>
            <button @click="toggleRecording" :class="isRecording ? 'btn-danger btn-sm' : 'btn-secondary btn-sm'">
              <component :is="isRecording ? Square : Play" class="h-3.5 w-3.5" :stroke-width="2" />
              {{ isRecording ? t('stop') : t('start') }}
            </button>
          </div>
          <div v-if="recordedUrl" class="pt-1">
            <audio :src="recordedUrl" controls></audio>
          </div>
        </div>

        <!-- CTA -->
        <div class="mt-5 pt-5 border-t border-line">
          <button @click="runDiagnosisFromSelected" :disabled="loading || !canRun" class="btn-primary w-full">
            <span v-if="loading" class="spinner"></span>
            <Activity v-else class="h-4 w-4" :stroke-width="2" />
            <span>{{ loading ? t('running') : t('run_diagnosis') }}</span>
          </button>
          <p v-if="!canRun" class="text-2xs text-ink-subtle mt-2 text-center">{{ t('pick_first') }}</p>
        </div>
      </section>

      <!-- STEP 3 · Diagnosis result -->
      <section class="card card-pad lg:col-span-4">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-3 min-w-0">
            <div class="icon-tile"><Activity class="h-5 w-5" :stroke-width="1.75" /></div>
            <div class="min-w-0">
              <h3 class="section-title truncate">{{ t('diagnosis') }}</h3>
              <p class="section-sub">{{ t('step') }} 3</p>
            </div>
          </div>
          <span class="step-badge">03</span>
        </div>

        <!-- Empty -->
        <div v-if="!result && !loading" class="text-center py-10 px-2">
          <div class="mx-auto h-14 w-14 rounded-2xl bg-surface-sunken grid place-items-center">
            <Search class="h-6 w-6 text-ink-subtle" :stroke-width="1.5" />
          </div>
          <p class="mt-4 text-sm text-ink-muted leading-relaxed">{{ t('empty_diagnosis') }}</p>
        </div>

        <!-- Loading -->
        <div v-else-if="loading" class="space-y-3">
          <div class="skeleton h-28"></div>
          <div class="skeleton h-4 w-3/4"></div>
          <div class="skeleton h-4 w-2/3"></div>
          <div class="skeleton h-4 w-1/2"></div>
        </div>

        <!-- Result -->
        <div v-else class="space-y-5 animate-fade-up">
          <!-- Confidence card -->
          <div class="rounded-2xl bg-brand-50 border border-brand-100 p-5 relative overflow-hidden">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="text-2xs uppercase tracking-wider text-brand-700 font-semibold">{{ t('most_likely') }}</div>
                <h4 class="text-xl sm:text-2xl font-semibold mt-1 text-ink leading-snug">{{ localizedDiseaseName }}</h4>
                <div class="text-xs text-ink-muted mt-2 flex items-center gap-1.5">
                  <BadgeCheck class="h-3.5 w-3.5 text-brand-600" :stroke-width="2" />
                  {{ t('fused_confidence') }} <span class="font-semibold text-ink tabular">{{ result.overall_confidence }}</span>
                </div>
                <div v-if="result.medication_suggestions?.icd10" class="text-2xs text-ink-subtle mt-1 font-mono">
                  {{ t('icd10') }}: {{ result.medication_suggestions.icd10 }}
                </div>
              </div>
              <!-- Ring chart -->
              <div class="w-20 h-20 shrink-0">
                <svg viewBox="0 0 36 36" class="w-20 h-20">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none" stroke="#ccfbf1" stroke-width="3" />
                  <path :d="progressArc" fill="none" stroke="#0d9488" stroke-width="3" stroke-linecap="round" />
                  <text x="18" y="20.5" text-anchor="middle" font-size="8" fill="#0f766e" font-weight="700">{{ numericConfidence }}%</text>
                </svg>
              </div>
            </div>
          </div>

          <!-- Model breakdown -->
          <div class="grid grid-cols-3 gap-2">
            <div v-for="m in modelBreakdownChips" :key="m.label"
                 class="rounded-xl bg-surface-alt border border-line p-3 text-center min-w-0">
              <div class="flex items-center justify-center gap-1 text-2xs uppercase tracking-wider text-ink-subtle">
                <component :is="m.icon" class="h-3 w-3" :stroke-width="2" />
                {{ m.label }}
              </div>
              <div class="text-2xs sm:text-xs font-semibold text-ink mt-1 truncate">{{ m.value || '—' }}</div>
            </div>
          </div>

          <!-- Probabilities -->
          <div v-if="result.all_disease_probabilities">
            <div class="flex items-center justify-between mb-2.5">
              <h4 class="text-sm font-semibold text-ink">{{ t('class_probabilities') }}</h4>
              <button class="text-xs text-brand-700 hover:text-brand-800 inline-flex items-center gap-1" @click="showAllProbs = !showAllProbs">
                {{ showAllProbs ? t('show_top_4') : t('show_all') }}
                <ChevronDown class="h-3 w-3 transition-transform" :class="showAllProbs && 'rotate-180'" :stroke-width="2" />
              </button>
            </div>
            <div class="space-y-2.5">
              <div v-for="row in visibleProbs" :key="row.name" class="text-xs">
                <div class="flex justify-between mb-1">
                  <div class="font-medium text-ink truncate pr-2">{{ row.name }}</div>
                  <div class="text-ink-muted tabular shrink-0">{{ row.value }}%</div>
                </div>
                <div class="w-full bg-surface-sunken h-1.5 rounded-full overflow-hidden">
                  <div class="bar-fill h-1.5 rounded-full bg-brand-500"
                       :style="{ '--w': row.value + '%', width: row.value + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Doctor summary + medications -->
    <div v-if="result" class="grid gap-5 sm:gap-6 grid-cols-1 lg:grid-cols-12 animate-fade-up">
      <!-- Doctor summary -->
      <section class="card card-pad lg:col-span-5">
        <div class="flex items-center gap-3 mb-4">
          <div class="icon-tile"><ClipboardList class="h-5 w-5" :stroke-width="1.75" /></div>
          <h3 class="section-title">{{ t('doctors_summary') }}</h3>
        </div>

        <p class="text-sm text-ink leading-relaxed">{{ overviewText }}</p>

        <div v-if="(result.doctor_summary?.recommended_precautions || []).length" class="mt-5">
          <h4 class="text-2xs font-semibold uppercase tracking-wider text-ink-subtle flex items-center gap-1.5">
            <ShieldCheck class="h-3.5 w-3.5" :stroke-width="2" />
            {{ t('recommended_precautions') }}
          </h4>
          <ul class="mt-2.5 space-y-2">
            <li v-for="(p, i) in result.doctor_summary.recommended_precautions" :key="'p'+i"
                class="text-sm text-ink leading-relaxed flex items-start gap-2.5">
              <Check class="h-4 w-4 text-brand-600 mt-0.5 shrink-0" :stroke-width="2.25" />
              <span>{{ p }}</span>
            </li>
          </ul>
        </div>

        <div v-if="treatmentGoals.length" class="mt-5">
          <h4 class="text-2xs font-semibold uppercase tracking-wider text-ink-subtle flex items-center gap-1.5">
            <Target class="h-3.5 w-3.5" :stroke-width="2" />
            {{ t('treatment_goals') }}
          </h4>
          <ul class="mt-2.5 space-y-2">
            <li v-for="(g, i) in treatmentGoals" :key="'g'+i"
                class="text-sm text-ink leading-relaxed flex items-start gap-2.5">
              <ChevronRight class="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" :stroke-width="2.25" />
              <span>{{ g }}</span>
            </li>
          </ul>
        </div>

        <div v-if="redFlags.length" class="mt-5 rounded-2xl bg-rose-50 border border-rose-200 p-4">
          <h4 class="text-2xs font-semibold uppercase tracking-wider text-rose-700 flex items-center gap-1.5">
            <AlertTriangle class="h-3.5 w-3.5" :stroke-width="2" />
            {{ t('red_flags') }}
          </h4>
          <ul class="mt-2.5 space-y-2">
            <li v-for="(f, i) in redFlags" :key="'rf'+i"
                class="text-sm text-rose-900 leading-relaxed flex items-start gap-2.5">
              <span class="mt-1.5 h-1.5 w-1.5 rounded-full bg-rose-500 shrink-0"></span>
              <span>{{ f }}</span>
            </li>
          </ul>
        </div>
      </section>

      <!-- Medications -->
      <section class="card card-pad lg:col-span-7">
        <!-- Header -->
        <div class="flex items-start justify-between mb-4 flex-wrap gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <div class="icon-tile"><Pill class="h-5 w-5" :stroke-width="1.75" /></div>
            <div class="min-w-0">
              <h3 class="section-title leading-tight">{{ t('ai_picks') }}</h3>
              <p class="section-sub line-clamp-2">{{ t('available_at') }}</p>
            </div>
          </div>
          <span v-if="result.medication_cards" class="pill pill-brand">
            <Sparkles class="h-3 w-3" :stroke-width="2" />
            {{ result.medication_cards.model || t('ai_model_label') }}
          </span>
        </div>

        <!-- AI picks -->
        <div v-if="aiCards.length" class="grid grid-cols-1 xl:grid-cols-2 gap-3">
          <article v-for="(c, i) in aiCards" :key="'ai'+i"
            class="rounded-2xl border border-line bg-surface hover:border-line-strong hover:shadow-soft transition-all duration-200 p-4 flex flex-col">
            <!-- Name + price/rx -->
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="font-semibold text-ink truncate">{{ isRTL ? c.name_ar : c.name }}</div>
                <div v-if="!isRTL" class="ar text-xs text-ink-subtle mt-0.5 truncate" dir="rtl">{{ c.name_ar }}</div>
                <div v-else class="text-xs text-ink-subtle mt-0.5 truncate" dir="ltr">{{ c.name }}</div>
              </div>
              <div class="text-right shrink-0">
                <div v-if="c.meta?.indicative_price_sar" class="text-sm font-semibold text-brand-700 tabular">
                  {{ c.meta.indicative_price_sar }} <span class="text-2xs font-normal text-ink-subtle">SAR</span>
                </div>
                <span class="mt-1 inline-flex" :class="c.meta?.rx_required ? 'pill pill-warn' : 'pill pill-success'">
                  {{ c.meta?.rx_required ? t('rx') : t('otc') }}
                </span>
              </div>
            </div>

            <!-- Classification badges -->
            <div class="flex flex-wrap items-center gap-1.5 mt-2.5">
              <span v-if="c.meta?.classification" class="pill border" :class="classBadge(legendFor(c.meta.classification)?.color)">
                {{ isRTL ? c.meta.classification_label_ar : c.meta.classification_label_en }}
              </span>
              <span v-if="c.meta?.evidence_level" class="pill pill-muted">
                {{ t('evidence_level') }}: {{ c.meta.evidence_level }}
              </span>
            </div>

            <!-- Description -->
            <p class="mt-3 text-xs text-ink-muted leading-relaxed">{{ isRTL ? c.description_ar : c.description }}</p>

            <!-- Why -->
            <div class="mt-3 rounded-xl bg-surface-alt border border-line p-3">
              <div class="text-2xs uppercase tracking-wider text-brand-700 font-semibold flex items-center gap-1">
                <Lightbulb class="h-3 w-3" :stroke-width="2" />
                {{ t('why_this') }}
              </div>
              <p class="text-xs text-ink leading-relaxed mt-1">{{ isRTL ? c.why_ar : c.why }}</p>
            </div>

            <!-- Bullets -->
            <ul class="mt-3 space-y-1.5">
              <li v-for="(b, j) in (isRTL ? c.bullets_ar : c.bullets)" :key="j"
                  class="text-xs text-ink-muted flex items-start gap-2">
                <Dot class="h-3 w-3 text-brand-600 mt-0.5 shrink-0" :stroke-width="3" />
                <span>{{ b }}</span>
              </li>
            </ul>

            <!-- Footer links -->
            <div class="mt-auto pt-3 flex flex-wrap items-center gap-1.5 border-t border-line/70">
              <a v-if="c.link" :href="c.link" target="_blank" rel="noopener" class="btn-primary btn-sm">
                <ExternalLink class="h-3 w-3" :stroke-width="2" />
                {{ t('view_product') }}
              </a>
              <a v-for="(e, k) in (c.extra_links || []).slice(0, 3)" :key="k"
                 :href="e.url" target="_blank" rel="noopener"
                 class="pill pill-muted hover:bg-stone-200 transition-colors">
                {{ isRTL ? e.label_ar : e.label }}
              </a>
            </div>
          </article>
        </div>

        <!-- Ranking signals -->
        <div v-if="result.medication_cards?.ranking_signals?.length" class="mt-3 text-2xs text-ink-subtle flex flex-wrap items-center gap-1.5">
          <span class="font-medium">{{ t('ranking_signals') }}:</span>
          <span v-for="(s, i) in result.medication_cards.ranking_signals" :key="i"
                class="px-1.5 py-0.5 rounded bg-surface-sunken text-ink-muted">{{ s }}</span>
        </div>

        <!-- Full catalogue toggle -->
        <div class="mt-5 pt-4 border-t border-line">
          <button class="btn-secondary btn-sm" @click="showCatalog = !showCatalog">
            <component :is="showCatalog ? ChevronUp : ChevronDown" class="h-3.5 w-3.5" :stroke-width="2" />
            {{ showCatalog ? t('hide_full_catalog') : t('show_full_catalog') }}
            <span class="text-ink-subtle">({{ filteredMeds.length }})</span>
          </button>
        </div>

        <!-- Catalogue -->
        <div v-if="showCatalog" class="mt-4 animate-fade-up">
          <!-- Pharmacy filter chips -->
          <div class="-mx-1 px-1 mb-3 overflow-x-auto no-scrollbar">
            <div class="flex items-center gap-1.5 w-max">
              <button v-for="p in pharmacyFilters" :key="p"
                @click="togglePharmacy(p)"
                :class="activePharmacies.includes(p)
                  ? 'pill bg-brand-600 text-white border border-brand-600 hover:bg-brand-700'
                  : 'pill pill-muted hover:bg-stone-200'"
                class="whitespace-nowrap transition-colors">
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

          <div v-if="filteredMeds.length === 0" class="text-sm text-ink-muted py-8 text-center">
            {{ t('no_meds') }}
          </div>

          <div class="grid grid-cols-1 xl:grid-cols-2 gap-3">
            <article v-for="(m, i) in filteredMeds" :key="i"
              class="rounded-2xl border border-line bg-surface hover:border-line-strong transition-colors p-4">
              <!-- Header -->
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="font-semibold text-ink truncate">{{ isRTL ? m.brand_ar : m.brand }}</div>
                  <div class="text-xs text-ink-subtle truncate">{{ isRTL ? (m.generic_ar || m.generic) : m.generic }}</div>
                  <div v-if="!isRTL" class="ar text-sm text-ink-muted mt-1 truncate" dir="rtl">{{ m.brand_ar }}</div>
                  <div v-else class="text-xs text-ink-subtle mt-1 truncate" dir="ltr">{{ m.brand }}</div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-sm font-semibold text-brand-700 tabular">{{ m.indicative_price_sar }} <span class="text-2xs font-normal text-ink-subtle">SAR</span></div>
                  <span class="mt-1 inline-flex" :class="m.rx_required ? 'pill pill-warn' : 'pill pill-success'">
                    {{ m.rx_required ? t('rx') : t('otc') }}
                  </span>
                </div>
              </div>

              <!-- Tags -->
              <div class="flex flex-wrap items-center gap-1.5 mt-3">
                <span v-if="legendFor(m.classification)"
                  class="pill border"
                  :class="classBadge(legendFor(m.classification).color)">
                  {{ isRTL ? legendFor(m.classification).ar : legendFor(m.classification).en }}
                </span>
                <span v-if="m.evidence_level" class="pill pill-muted">
                  {{ t('evidence_level') }}: {{ m.evidence_level }}
                </span>
                <span v-if="m.age_group" class="pill pill-muted">
                  {{ t('age_group') }}: {{ ageLabel(m.age_group) }}
                </span>
                <span v-if="m.category" class="pill pill-muted">
                  {{ m.category }}
                </span>
              </div>

              <!-- Expand toggle -->
              <button class="mt-3 text-xs text-brand-700 hover:text-brand-800 inline-flex items-center gap-1" @click="toggleExpand(i)">
                <component :is="expanded[i] ? ChevronUp : ChevronDown" class="h-3 w-3" :stroke-width="2" />
                {{ expanded[i] ? t('collapse') : t('expand') }}
              </button>

              <div v-if="expanded[i]" class="mt-3 space-y-3 text-xs animate-fade-up">
                <div>
                  <div class="text-2xs uppercase tracking-wider text-ink-subtle font-medium">{{ t('mechanism') }}</div>
                  <p class="text-ink-muted leading-relaxed mt-0.5">{{ isRTL ? m.mechanism_ar : m.mechanism_en }}</p>
                </div>
                <div>
                  <div class="text-2xs uppercase tracking-wider text-ink-subtle font-medium">{{ t('dosage') }}</div>
                  <p class="text-ink-muted leading-relaxed mt-0.5">{{ isRTL ? m.dosage_hint_ar : m.dosage_hint_en }}</p>
                </div>
                <div>
                  <div class="text-2xs uppercase tracking-wider text-ink-subtle font-medium">{{ t('side_effects') }}</div>
                  <p class="text-ink-muted leading-relaxed mt-0.5">{{ isRTL ? m.side_effects_ar : m.side_effects_en }}</p>
                </div>
                <div>
                  <div class="text-2xs uppercase tracking-wider text-ink-subtle font-medium">{{ t('contraindications') }}</div>
                  <p class="text-ink-muted leading-relaxed mt-0.5">{{ isRTL ? m.contraindications_ar : m.contraindications_en }}</p>
                </div>
                <div v-if="m.sources_resolved && m.sources_resolved.length">
                  <div class="text-2xs uppercase tracking-wider text-ink-subtle font-medium">{{ t('sources') }}</div>
                  <ul class="mt-1 space-y-0.5">
                    <li v-for="src in m.sources_resolved" :key="src.id">
                      <a :href="src.url" target="_blank" rel="noopener"
                         class="text-brand-700 hover:text-brand-800 inline-flex items-center gap-1">
                        <ExternalLink class="h-3 w-3" :stroke-width="2" />
                        {{ isRTL ? src.name_ar : src.name_en }}
                      </a>
                    </li>
                  </ul>
                </div>
              </div>

              <!-- Pharmacy footer -->
              <div class="flex flex-wrap items-center justify-end gap-1 mt-3 pt-3 border-t border-line/70">
                <span v-for="ph in m.pharmacies" :key="ph" class="pill pill-muted">{{ pharmacyLabel(ph) }}</span>
              </div>
            </article>
          </div>
        </div>

        <!-- Disclaimer -->
        <div v-if="result.medication_suggestions" class="mt-5 rounded-2xl bg-amber-50 border border-amber-200 p-3.5 text-xs text-amber-900 flex items-start gap-2.5">
          <Info class="h-4 w-4 text-amber-700 mt-0.5 shrink-0" :stroke-width="2" />
          <div v-if="!isRTL">{{ result.medication_suggestions.disclaimer_en }}</div>
          <div v-else dir="rtl" class="ar">{{ result.medication_suggestions.disclaimer_ar }}</div>
        </div>
      </section>
    </div>

    <!-- Data sources -->
    <section v-if="result && primarySources.length" class="card card-pad animate-fade-up">
      <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div class="icon-tile"><BookOpen class="h-5 w-5" :stroke-width="1.75" /></div>
          <div class="min-w-0">
            <h3 class="section-title">{{ t('data_sources_title') }}</h3>
            <p class="section-sub">{{ t('data_sources_desc') }}</p>
          </div>
        </div>
        <button class="btn-secondary btn-sm" @click="showSources = !showSources">
          <component :is="showSources ? ChevronUp : ChevronDown" class="h-3.5 w-3.5" :stroke-width="2" />
          {{ showSources ? t('collapse') : t('expand') }}
        </button>
      </div>
      <div v-if="showSources" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 animate-fade-up">
        <a v-for="src in primarySources" :key="src.id" :href="src.url" target="_blank" rel="noopener"
           class="rounded-2xl border border-line bg-surface hover:border-brand-500 hover:shadow-soft transition-all duration-200 p-4 block group">
          <div class="flex items-center justify-between">
            <div class="text-2xs uppercase tracking-wider text-ink-subtle font-medium">{{ src.type }}</div>
            <ExternalLink class="h-3.5 w-3.5 text-ink-subtle group-hover:text-brand-600 transition-colors" :stroke-width="1.75" />
          </div>
          <div class="text-sm font-semibold text-ink mt-1.5 leading-snug">{{ isRTL ? src.name_ar : src.name_en }}</div>
          <div class="text-2xs text-brand-700 truncate mt-1 font-mono">{{ src.url }}</div>
        </a>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import axios from 'axios'
import { t, locale, isRTL } from '../i18n.js'
import {
  Stethoscope, AudioLines, Activity, BadgeCheck, Mic, Upload, UploadCloud,
  FileAudio, Pill, ShieldCheck, AlertTriangle, ClipboardList, Target,
  Sparkles, Search, ChevronDown, ChevronUp, ChevronRight, ExternalLink,
  Info, BookOpen, Lightbulb, Check, Dot, Play, Square, User,
  HeartPulse, MessageSquareText, Volume2
} from 'lucide-vue-next'

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
const showCatalog = ref(false)
const expanded = reactive({})

const pharmacyFilters = ['Nahdi', 'Al-Dawaa', 'Al-Mamlaka', 'Whites', 'Innova', 'Bin Dawood', 'Tadawi', 'Boots']
const activePharmacies = ref([...pharmacyFilters])

const PHARMACY_AR = {
  'Nahdi': 'النهدي',
  'Al-Dawaa': 'الدواء',
  'Al-Mamlaka': 'المملكة',
  'Whites': 'وايتس',
  'Innova': 'إنوفا',
  'Bin Dawood': 'بن داود',
  'Tadawi': 'تداوي',
  'Boots': 'بوتس'
}
function pharmacyLabel(p) { return isRTL.value ? (PHARMACY_AR[p] || p) : p }
function ageLabel(g) {
  if (g === 'adult') return t('age_adult')
  if (g === 'pediatric') return t('age_pediatric')
  return t('age_all')
}

const modelChips = computed(() => [
  { icon: Volume2,            label: t('pipeline_audio'),    model: 'CNN' },
  { icon: HeartPulse,         label: t('pipeline_vitals'),   model: 'RandomForest' },
  { icon: MessageSquareText,  label: t('pipeline_symptoms'), model: 'NLP' }
])

const modelBreakdownChips = computed(() => [
  { icon: Volume2,           label: t('audio_cnn'),     value: result.value?.model_breakdown?.audio_cnn_prediction },
  { icon: HeartPulse,        label: t('vitals_rf'),     value: result.value?.model_breakdown?.vitals_rf_prediction },
  { icon: MessageSquareText, label: t('symptoms_nlp'),  value: result.value?.model_breakdown?.symptoms_nlp_prediction }
])

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

const aiCards = computed(() => result.value?.medication_cards?.cards || [])

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

function classBadge(color) {
  const base = {
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    indigo:  'bg-indigo-50 text-indigo-700 border-indigo-200',
    rose:    'bg-rose-50 text-rose-700 border-rose-200',
    blue:    'bg-blue-50 text-blue-700 border-blue-200',
    violet:  'bg-violet-50 text-violet-700 border-violet-200',
    amber:   'bg-amber-50 text-amber-700 border-amber-200',
    slate:   'bg-stone-50 text-stone-600 border-stone-200',
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
