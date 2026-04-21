<template>
  <div class="grid gap-6 lg:grid-cols-3">
    <!-- Left: Patient Profile -->
    <section class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">Patient Profile</h2>

      <div class="space-y-3">
        <div>
          <label class="block text-sm text-slate-600">Age</label>
          <input v-model.number="profile.age" type="number" min="0" step="0.1" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2" />
        </div>

        <div>
          <label class="block text-sm text-slate-600">Sex</label>
          <select v-model.number="profile.sex" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2">
            <option :value="1">Male</option>
            <option :value="0">Female</option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-slate-600">BMI</label>
            <input v-model.number="profile.bmi" type="number" step="0.1" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2" />
          </div>
          <div>
            <label class="block text-sm text-slate-600">SpO₂ (%)</label>
            <input v-model.number="profile.spo2" type="number" step="0.1" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-slate-600">Temperature (°C)</label>
            <input v-model.number="profile.temperature" type="number" step="0.1" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2" />
          </div>
          <div>
            <label class="block text-sm text-slate-600">Smoker</label>
            <select v-model.number="profile.smoker" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2">
              <option :value="0">No</option>
              <option :value="1">Yes</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-sm text-slate-600">Patient Symptoms / Notes</label>
          <textarea v-model="profile.patient_notes" rows="5" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2"></textarea>
        </div>
      </div>
    </section>

    <!-- Middle: Audio Controller -->
    <section class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">Audio Source</h2>

      <div class="mb-4">
        <nav class="flex space-x-2">
          <button :class="tab === 'sample' ? 'bg-accent text-white' : 'bg-slate-100'" @click="setTab('sample')" class="px-3 py-1 rounded">Select Sample</button>
          <button :class="tab === 'upload' ? 'bg-accent text-white' : 'bg-slate-100'" @click="setTab('upload')" class="px-3 py-1 rounded">Upload File</button>
          <button :class="tab === 'record' ? 'bg-accent text-white' : 'bg-slate-100'" @click="setTab('record')" class="px-3 py-1 rounded">Record</button>
        </nav>
      </div>

      <div v-if="tab === 'sample'" class="space-y-3">
        <label class="block text-sm text-slate-600">Choose a demo sample</label>
        <select v-model="selectedSample" class="mt-1 block w-full rounded border-gray-200 shadow-sm p-2">
          <option disabled value="">-- select sample --</option>
          <option v-for="s in sampleFiles" :key="s.filename" :value="s.filename">{{ s.label }} — {{ s.filename }}</option>
        </select>

        <div class="text-sm text-slate-500">Samples are read from the server's data folder.</div>

        <div v-if="selectedSample" class="pt-3 flex gap-2">
          <audio v-if="serverAudioUrl" :src="serverAudioUrl" controls class="flex-1"></audio>
          <button @click="runWithSample" class="px-4 py-2 bg-accent text-white rounded">Use Sample for Diagnosis</button>
        </div>
      </div>

      <div v-if="tab === 'upload'" class="space-y-3">
        <label class="block text-sm text-slate-600">Upload a WAV file</label>
        <input type="file" accept="audio/*" @change="onFileSelected" />
        <div v-if="localAudioUrl" class="pt-3">
          <audio :src="localAudioUrl" controls class="w-full"></audio>
          <div class="mt-2">
            <button @click="uploadSelectedFile" class="px-4 py-2 bg-accent text-white rounded">Upload & Use</button>
          </div>
        </div>
      </div>

      <div v-if="tab === 'record'" class="space-y-3">
        <div class="flex items-center gap-3">
          <button @click="toggleRecording" :class="isRecording ? 'bg-red-500' : 'bg-green-500'" class="text-white px-4 py-2 rounded">{{ isRecording ? 'Stop' : 'Start' }} Recording</button>
          <div v-if="recordedBlob" class="text-sm text-slate-600">Recorded — ready to upload</div>
        </div>

        <div v-if="recordedUrl" class="pt-3">
          <audio :src="recordedUrl" controls class="w-full"></audio>
          <div class="mt-2">
            <button @click="uploadRecorded" class="px-4 py-2 bg-accent text-white rounded">Upload Recording</button>
          </div>
        </div>
      </div>

      <!-- Action -->
      <div class="mt-6">
        <button @click="runDiagnosisFromSelected" :disabled="loading" class="w-full flex items-center justify-center gap-3 px-4 py-3 bg-slate-900 text-white rounded">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? 'Running AI Diagnosis...' : 'Run AI Diagnosis' }}</span>
        </button>
      </div>
    </section>

    <!-- Right: Results -->
    <section class="bg-white rounded-lg shadow p-6 lg:col-span-1 lg:col-start-3">
      <h2 class="text-lg font-semibold mb-4">Results</h2>

      <div v-if="result" class="space-y-4">
        <div class="bg-slate-50 p-4 rounded">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xl font-bold">{{ result.final_diagnosis }}</h3>
              <div class="text-sm text-slate-500">Confidence: {{ result.overall_confidence }}</div>
            </div>
            <div class="w-24 h-24 flex items-center justify-center">
              <svg viewBox="0 0 36 36" class="w-20 h-20">
                <path class="text-slate-200" d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#e6eef0" stroke-width="3.5"></path>
                <path :d="progressArc" fill="none" stroke="#06b6d4" stroke-width="3.5" stroke-linecap="round"></path>
                <text x="18" y="20.35" class="text-sm" text-anchor="middle" font-size="6" fill="#0f172a">{{ numericConfidence }}%</text>
              </svg>
            </div>
          </div>
        </div>

        <div>
          <h4 class="font-semibold">Doctor's Summary</h4>
          <p class="mt-2 text-sm text-slate-700">{{ result.doctor_summary?.disease_description }}</p>
          <ul class="list-disc ml-5 mt-2 text-sm text-slate-700">
            <li v-for="(p, i) in result.doctor_summary?.recommended_precautions || []" :key="i">{{ p }}</li>
          </ul>
        </div>

        <div>
          <h4 class="font-semibold">Model Breakdown</h4>
          <div class="flex gap-2 mt-2">
            <span class="px-3 py-1 bg-slate-100 rounded">Audio CNN: {{ result.model_breakdown?.audio_cnn_prediction }}</span>
            <span class="px-3 py-1 bg-slate-100 rounded">Vitals RF: {{ result.model_breakdown?.vitals_rf_prediction }}</span>
            <span class="px-3 py-1 bg-slate-100 rounded">NLP: {{ result.model_breakdown?.symptoms_nlp_prediction }}</span>
          </div>
        </div>

        <div>
          <h4 class="font-semibold">Probabilities</h4>
          <div class="mt-2 space-y-2">
            <div v-for="(v, k) in result.all_disease_probabilities" :key="k" class="text-sm">
              <div class="flex justify-between">
                <div>{{ k }}</div>
                <div class="text-slate-500">{{ v }}%</div>
              </div>
              <div class="w-full bg-slate-100 h-3 rounded mt-1">
                <div class="h-3 rounded bg-accent" :style="{ width: v + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-sm text-slate-500">Run a diagnosis to see results here.</div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const axiosInstance = axios.create({ baseURL: API_BASE })

const profile = ref({
  age: 35,
  sex: 1,
  bmi: 25.0,
  spo2: 98.0,
  temperature: 36.6,
  smoker: 0,
  patient_notes: 'Productive cough for 3 days.'
})

const tab = ref('sample')
const sampleFiles = ref([
  { label: 'Healthy Sample', filename: '101_1b1_Al_sc_Meditron.wav' },
  { label: 'COPD Sample', filename: '107_2b3_Pr_mc_AKGC417L.wav' },
  { label: 'Pneumonia Sample', filename: '109_1b1_Pr_sc_Litt3200.wav' }
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

const serverAudioUrl = computed(() => selectedSample.value ? `${API_BASE}/audio/${encodeURIComponent(selectedSample.value)}` : null)

function setTab(name) { tab.value = name }

function onFileSelected(e) {
  const f = e.target.files?.[0]
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

async function uploadSelectedFile() {
  if (!selectedFile.value) return alert('Choose a file first')
  loading.value = true
  try {
    const filename = await uploadFile(selectedFile.value)
    await runDiagnosis(filename)
  } catch (err) {
    alert('Upload failed: ' + err)
  } finally {
    loading.value = false
  }
}

async function uploadRecorded() {
  if (!recordedBlob.value) return
  loading.value = true
  try {
    const file = new File([recordedBlob.value], 'recording.wav', { type: 'audio/wav' })
    const filename = await uploadFile(file)
    await runDiagnosis(filename)
  } catch (err) {
    alert('Upload failed: ' + err)
  } finally {
    loading.value = false
  }
}

function toggleRecording() {
  if (isRecording.value) {
    mediaRecorder?.stop()
  } else {
    startRecording()
  }
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

async function runWithSample() {
  if (!selectedSample.value) return alert('Select a sample')
  loading.value = true
  try { await runDiagnosis(selectedSample.value) } catch (err) { alert('Diagnosis failed: ' + err) } finally { loading.value = false }
}

async function runDiagnosisFromSelected() {
  if (tab.value === 'sample') return runWithSample()
  if (tab.value === 'upload') return uploadSelectedFile()
  if (tab.value === 'record') return uploadRecorded()
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
  } catch (err) {
    console.error(err)
    alert('API error: ' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const numericConfidence = computed(() => {
  if (!result.value || !result.value.overall_confidence) return 0
  const text = String(result.value.overall_confidence).replace('%', '')
  const v = parseFloat(text)
  return Number.isFinite(v) ? Math.round(v) : 0
})

const progressArc = computed(() => {
  const pct = Math.max(0, Math.min(100, numericConfidence.value))
  const angle = (pct / 100) * 360
  const large = angle > 180 ? 1 : 0
  const radius = 15.9155
  const start = polarToCartesian(18, 18, radius, 0)
  const end = polarToCartesian(18, 18, radius, angle)
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${large} 1 ${end.x} ${end.y}`
})

function polarToCartesian(cx, cy, r, angleDeg) { const angleRad = (angleDeg - 90) * Math.PI / 180.0; return { x: cx + (r * Math.cos(angleRad)), y: cy + (r * Math.sin(angleRad)) } }
</script>

<style scoped>
/* small style adjustments */
.bg-accent { background-color: #06b6d4 }
.spinner { width: 1rem; height: 1rem; border-radius: 9999px; border: 2px solid rgba(0,0,0,0.08); border-top-color: rgba(0,0,0,0.6); animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>