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
  spo2:                    { en: 'SpO₂ (%)',                                ar: 'تشبّع الأكسجين %' },
  temperature:             { en: 'Temperature (°C)',                        ar: 'درجة الحرارة °م' },
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
  select_placeholder:      { en: 'Select a respiratory sample…',            ar: 'اختر عيّنة تنفسية…' },
  samples_hint:            { en: 'Pre-recorded breath sounds curated for demo purposes.',
                              ar: 'أصوات تنفّس مسجّلة مسبقاً لأغراض العرض التوضيحي.' },

  // Disease labels — used by the sample picker and elsewhere
  disease_healthy:         { en: 'Healthy',                                 ar: 'صحي' },
  disease_copd:            { en: 'COPD',                                    ar: 'الانسداد الرئوي المزمن' },
  disease_asthma:          { en: 'Asthma',                                  ar: 'الربو' },
  disease_bronchiectasis:  { en: 'Bronchiectasis',                          ar: 'توسّع القصبات' },
  disease_pneumonia:       { en: 'Pneumonia',                               ar: 'الالتهاب الرئوي' },
  disease_urti:            { en: 'Upper Respiratory Infection',             ar: 'التهاب الجهاز التنفسي العلوي' },
  disease_lrti:            { en: 'Lower Respiratory Infection',             ar: 'التهاب الجهاز التنفسي السفلي' },
  disease_bronchiolitis:   { en: 'Bronchiolitis',                           ar: 'التهاب القصيبات' },

  // Short clinical hints for each sample (one line each)
  hint_healthy:            { en: 'Normal vesicular breath sounds',          ar: 'تنفّس طبيعي بدون أصوات شاذة' },
  hint_copd:               { en: 'Wheezing, prolonged expiration',          ar: 'صفير وزفير ممتد' },
  hint_asthma:             { en: 'Expiratory wheeze, airway narrowing',     ar: 'صفير زفيري وضيق في الشُّعب' },
  hint_bronchiectasis:     { en: 'Coarse crackles, productive cough',       ar: 'فرقعات خشنة وسعال منتج' },
  hint_pneumonia:          { en: 'Crackles, bronchial breath sounds',       ar: 'فرقعات وأصوات تنفّس قصبي' },
  hint_urti:               { en: 'Nasal congestion, mild upper-airway noise', ar: 'احتقان أنفي وضوضاء خفيفة' },
  hint_lrti:               { en: 'Coarse rhonchi, lower-airway involvement', ar: 'حشرجات خشنة في المجاري السفلية' },
  hint_bronchiolitis:      { en: 'Diffuse wheezing, typical in infants',    ar: 'صفير منتشر، شائع لدى الرضّع' },
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
                              ar: 'اختر عيّنة أو ارفع ملفاً أو سجّل أولاً.' },

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
  available_at:            { en: 'Top Saudi chains: Nahdi · Al-Dawaa · Al-Mamlaka · Whites · Innova · Bin Dawood · Tadawi · Boots',
                              ar: 'أشهر الصيدليات السعودية: النهدي · الدواء · المملكة · وايتس · إنوفا · بن داود · تداوي · بوتس' },
  no_meds:                 { en: 'No medications match this disease/filter combination.',
                              ar: 'لا توجد أدوية تطابق المرض المحدد أو خيارات التصفية.' },
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
  age_all:                 { en: 'All ages',                                ar: 'كل الأعمار' },

  ai_picks:                { en: 'AI-ranked picks',                          ar: 'الترشيحات بالذكاء الاصطناعي' },
  ai_model_label:          { en: 'TF-IDF + ranker',                          ar: 'TF-IDF + نموذج ترتيب' },
  why_this:                { en: 'Why this medicine',                        ar: 'لماذا هذا الدواء' },
  view_product:            { en: 'View product',                             ar: 'عرض المنتج' },
  view_on:                 { en: 'View on',                                  ar: 'عرض على' },
  also_search_on:          { en: 'Also search on',                           ar: 'ابحث أيضاً على' },
  ranking_signals:         { en: 'Ranking signals used',                     ar: 'إشارات الترتيب المستخدمة' },
  full_catalog:            { en: 'Full curated catalogue',                   ar: 'الكتالوج الكامل' },
  show_full_catalog:       { en: 'Show full catalogue',                      ar: 'إظهار الكتالوج الكامل' },
  hide_full_catalog:       { en: 'Hide full catalogue',                      ar: 'إخفاء الكتالوج الكامل' },

  // Top-level tab navigation
  tab_triage:              { en: 'Triage',                                   ar: 'الفحص' },
  tab_chat:                { en: 'Doctor Assistant',                         ar: 'مساعد الطبيب' },

  // Doctor chat
  chat_title:              { en: 'Doctor Assistant',                         ar: 'مساعد الطبيب' },
  chat_subtitle:           { en: 'Ask about symptoms, differentials, and medication recommendations. Bilingual.',
                              ar: 'اسأل عن الأعراض والتشخيصات التفريقية واقتراحات الأدوية. ثنائي اللغة.' },
  chat_empty_title:        { en: 'Start a clinical conversation',            ar: 'ابدأ محادثة سريرية' },
  chat_empty_desc:         { en: 'Try one of the prompts below or type your own question.',
                              ar: 'جرّب أحد الأمثلة أدناه أو اكتب سؤالك الخاص.' },
  chat_placeholder:        { en: 'Describe symptoms, ask about a medication, request a differential…',
                              ar: 'صف الأعراض، اسأل عن دواء، اطلب تشخيصاً تفريقياً…' },
  chat_send:               { en: 'Send',                                     ar: 'إرسال' },
  chat_thinking:           { en: 'Thinking…',                                ar: 'يفكر…' },
  chat_clear:              { en: 'Clear chat',                               ar: 'مسح المحادثة' },
  chat_you:                { en: 'You',                                      ar: 'أنت' },
  chat_assistant:          { en: 'Assistant',                                ar: 'المساعد' },
  chat_disclaimer:         { en: 'Decision support only — verify against current guidelines and exercise clinical judgement.',
                              ar: 'أداة دعم قرار — راجع الإرشادات السريرية الحالية واستخدم حكمك الطبي.' },
  chat_send_hint:          { en: 'Enter to send · Shift+Enter for new line', ar: 'Enter للإرسال · Shift+Enter لسطر جديد' },
  chat_error_503:          { en: 'AI provider not reachable. Verify HF_TOKEN in .env and that the model is available.',
                              ar: 'تعذّر الوصول إلى مزود الذكاء الاصطناعي. تحقّق من HF_TOKEN في ملف ‎.env وأن النموذج متاح.' },
  chat_error_generic:      { en: 'Something went wrong while contacting the assistant.',
                              ar: 'حدث خطأ أثناء التواصل مع المساعد.' },
  chat_example_1:          { en: 'First-line antibiotic for community-acquired pneumonia in a 65 y/o, no allergies?',
                              ar: 'ما الخيار الأول من المضادات الحيوية للالتهاب الرئوي المكتسب من المجتمع في مريض ٦٥ سنة بدون حساسية؟' },
  chat_example_2:          { en: 'Differential for productive cough + low-grade fever + weight loss over 3 weeks.',
                              ar: 'التشخيص التفريقي لسعال منتج مع حرارة خفيفة وفقدان وزن خلال ٣ أسابيع.' },
  chat_example_3:          { en: 'Safe analgesic in a patient with CKD stage 3 and hypertension?',
                              ar: 'ما المسكن الآمن لمريض يعاني من قصور كلوي مزمن (مرحلة ٣) وارتفاع ضغط الدم؟' },

  // Settings / key banner
  no_key_title:            { en: 'AI provider not configured',               ar: 'لم يتم إعداد مزود الذكاء الاصطناعي' },
  no_key_desc:             { en: 'Add your free Hugging Face token to .env (HF_TOKEN=hf_…) and restart the server to enable Arabic translation and the doctor chat.',
                              ar: 'أضف رمز Hugging Face المجاني إلى ملف ‎.env (HF_TOKEN=hf_…) ثم أعد تشغيل الخادم لتفعيل الترجمة والمساعد الطبي.' }
}

export function t(key) {
  const entry = dict[key]
  if (!entry) return key
  return entry[locale.value] || entry.en || key
}
