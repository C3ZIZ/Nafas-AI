// Lightweight i18n for Nafas AI dashboard. Two locales only: en, ar.
// Each key has both a language and an isRTL flag. Used by App.vue and Dashboard.vue.

import { ref, computed } from 'vue'

export const LOCALES = {
  en: { label: 'English', dir: 'ltr', flag: 'EN' },
  ar: { label: 'العربية', dir: 'rtl', flag: 'AR' }
}

export const locale = ref(localStorage.getItem('nafas-locale') || 'en')

export function setLocale(l) {
  if (!LOCALES[l]) return
  locale.value = l
  localStorage.setItem('nafas-locale', l)
  document.documentElement.dir = LOCALES[l].dir
  document.documentElement.lang = l
}

// Initialise document direction on load
setLocale(locale.value)

export const isRTL = computed(() => LOCALES[locale.value]?.dir === 'rtl')

const dict = {
  app_title:               { en: 'Nafas AI',                                ar: 'نَفَس AI' },
  app_subtitle:            { en: 'Multi-modal Respiratory Triage',          ar: 'تشخيص تنفسي متعدد المصادر' },
  api_live:                { en: 'API live',                                ar: 'الخدمة تعمل' },
  footer:                  { en: 'Educational decision-support · not a substitute for clinical judgement',
                              ar: 'أداة دعم قرار تعليمية · لا تُغني عن استشارة الطبيب' },

  hero_title:              { en: 'Run a triage session',                    ar: 'ابدأ جلسة فحص' },
  hero_desc:               { en: 'Combine breath audio · vitals · symptoms — get a fused diagnosis with Saudi pharmacy medication suggestions.',
                              ar: 'ادمج صوت التنفس والمؤشرات الحيوية والأعراض للحصول على تشخيص موحّد مع اقتراحات دواء من الصيدليات السعودية.' },
  pipeline_audio:          { en: 'Audio',                                   ar: 'الصوت' },
  pipeline_vitals:         { en: 'Vitals',                                  ar: 'المؤشرات' },
  pipeline_symptoms:       { en: 'Symptoms',                                ar: 'الأعراض' },

  step:                    { en: 'Step',                                    ar: 'خطوة' },

  patient_profile:         { en: 'Patient Profile',                         ar: 'بيانات المريض' },
  age:                     { en: 'Age',                                     ar: 'العمر' },
  sex:                     { en: 'Sex',                                     ar: 'الجنس' },
  male:                    { en: 'Male',                                    ar: 'ذكر' },
  female:                  { en: 'Female',                                  ar: 'أنثى' },
  bmi:                     { en: 'BMI',                                     ar: 'كتلة الجسم' },
  spo2:                    { en: 'SpO₂ (%)',                                ar: 'الأكسجين %' },
  temperature:             { en: 'Temperature (°C)',                        ar: 'الحرارة °م' },
  smoker:                  { en: 'Smoker',                                  ar: 'مدخن' },
  yes:                     { en: 'Yes',                                     ar: 'نعم' },
  no:                      { en: 'No',                                      ar: 'لا' },
  patient_notes:           { en: 'Patient symptoms / notes',                ar: 'أعراض وملاحظات المريض' },
  patient_notes_placeholder: { en: 'e.g. Productive cough for 3 days, chest tightness, fever at night…',
                              ar: 'مثلاً: سعال مع بلغم منذ ٣ أيام، ضيق صدر، حرارة ليلية…' },

  audio_source:            { en: 'Audio Source',                            ar: 'مصدر الصوت' },
  tab_sample:              { en: 'Sample',                                  ar: 'عيّنة' },
  tab_upload:              { en: 'Upload',                                  ar: 'رفع' },
  tab_record:              { en: 'Record',                                  ar: 'تسجيل' },
  choose_sample:           { en: 'Choose a demo sample',                    ar: 'اختر عيّنة' },
  select_placeholder:      { en: '— select sample —',                       ar: '— اختر عيّنة —' },
  samples_hint:            { en: 'Samples are read directly from the server data folder.',
                              ar: 'يتم تحميل العيّنات من مجلد بيانات الخادم.' },
  click_to_upload:         { en: 'Click to upload',                         ar: 'اضغط للرفع' },
  or_drag_drop:            { en: 'or drag & drop',                          ar: 'أو اسحب وأفلت الملف' },
  file_types:              { en: '.wav · .mp3 · .m4a · .flac',              ar: '.wav · .mp3 · .m4a · .flac' },
  recording:               { en: 'Recording…',                              ar: 'جاري التسجيل…' },
  mic_idle:                { en: 'Microphone idle',                         ar: 'الميكروفون جاهز' },
  mic_hint:                { en: 'Use a quiet room and breathe gently into the mic.',
                              ar: 'سجّل في مكان هادئ وتنفّس بهدوء قرب الميكروفون.' },
  start:                   { en: 'Start',                                   ar: 'ابدأ' },
  stop:                    { en: 'Stop',                                    ar: 'إيقاف' },
  run_diagnosis:           { en: 'Run AI diagnosis',                        ar: 'تشغيل التشخيص' },
  running:                 { en: 'Running multi-modal AI…',                 ar: 'جاري التحليل…' },
  pick_first:              { en: 'Pick a sample, upload, or record audio first.',
                              ar: 'اختر عيّنة أو ارفع ملف أو سجّل أولاً.' },

  diagnosis:               { en: 'Diagnosis',                               ar: 'التشخيص' },
  empty_diagnosis:         { en: 'Run a diagnosis to see the fused result, model breakdown, and pharmacy suggestions.',
                              ar: 'شغّل التشخيص لتظهر النتيجة الموحّدة وتفاصيل النماذج واقتراحات الصيدلية.' },
  most_likely:             { en: 'Most likely',                             ar: 'الأرجح' },
  fused_confidence:        { en: 'Fused confidence',                        ar: 'الثقة الموحّدة' },
  audio_cnn:               { en: 'Audio CNN',                               ar: 'الصوت CNN' },
  vitals_rf:               { en: 'Vitals RF',                               ar: 'المؤشرات RF' },
  symptoms_nlp:            { en: 'Symptoms NLP',                            ar: 'الأعراض NLP' },
  class_probabilities:     { en: 'Class probabilities',                     ar: 'احتمالات التصنيف' },
  show_top_4:              { en: 'Show top 4',                              ar: 'أعلى ٤ فقط' },
  show_all:                { en: 'Show all',                                ar: 'عرض الكل' },

  doctors_summary:         { en: "Doctor's Summary",                        ar: 'ملخص الطبيب' },
  recommended_precautions: { en: 'Recommended precautions',                 ar: 'الإجراءات الموصى بها' },
  treatment_goals:         { en: 'Treatment goals',                         ar: 'أهداف العلاج' },
  red_flags:               { en: 'Red flags — seek care immediately',       ar: 'علامات خطر — راجع الطوارئ' },
  icd10:                   { en: 'ICD-10',                                  ar: 'تصنيف ICD-10' },

  pharmacy_suggestions:    { en: 'Saudi Pharmacy Suggestions',              ar: 'اقتراحات الصيدليات السعودية' },
  available_at:            { en: 'Available at Nahdi · Al-Dawaa · Al-Mamlaka',
                              ar: 'متوفرة في النهدي · الدواء · المملكة' },
  no_meds:                 { en: 'No medications match this disease/filter combination.',
                              ar: 'لا توجد أدوية تطابق هذا المرض أو هذا الفلتر.' },
  rx:                      { en: 'Rx',                                      ar: 'وصفة' },
  otc:                     { en: 'OTC',                                     ar: 'بدون وصفة' },
  mechanism:               { en: 'Mechanism',                               ar: 'آلية العمل' },
  dosage:                  { en: 'Dosage',                                  ar: 'الجرعة' },
  side_effects:            { en: 'Side effects',                            ar: 'الآثار الجانبية' },
  contraindications:       { en: 'Contraindications',                       ar: 'موانع الاستخدام' },
  age_group:               { en: 'Age group',                               ar: 'الفئة العمرية' },
  evidence_level:          { en: 'Evidence',                                ar: 'مستوى الدليل' },
  sources:                 { en: 'Sources',                                 ar: 'المصادر' },
  data_sources_title:      { en: 'Data sources & integrity',                ar: 'مصادر البيانات والموثوقية' },
  data_sources_desc:       { en: 'Every disease and medication entry is referenced. Tap a source to open it.',
                              ar: 'جميع الأمراض والأدوية مدعومة بمصادر مرجعية. اضغط على المصدر لفتحه.' },
  collapse:                { en: 'Hide details',                            ar: 'إخفاء التفاصيل' },
  expand:                  { en: 'Show details',                            ar: 'عرض التفاصيل' },

  age_adult:               { en: 'Adult',                                   ar: 'بالغ' },
  age_pediatric:           { en: 'Paediatric',                              ar: 'أطفال' },
  age_all:                 { en: 'All ages',                                ar: 'كل الأعمار' }
}

export function t(key) {
  const entry = dict[key]
  if (!entry) return key
  return entry[locale.value] || entry.en || key
}
