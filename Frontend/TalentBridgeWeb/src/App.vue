<script setup>
import { computed, onMounted, ref } from 'vue'
import { adminApi } from './modules/admin/admin.api'
import { applicationsApi } from './modules/applications/applications.api'
import { authApi } from './modules/auth/auth.api'
import { companiesApi } from './modules/companies/companies.api'
import { cvApi } from './modules/cv/cv.api'
import { jobsApi } from './modules/jobs/jobs.api'
import { matchingApi } from './modules/matching/matching.api'
import { notificationsApi } from './modules/notifications/notifications.api'
import { candidatesApi } from './modules/profiles/candidates.api'
import { profilesApi } from './modules/profiles/profiles.api'
import { authStore } from './stores/authStore'

const email = ref('candidate@talentbridge.local')
const password = ref('candidate123')
const loading = ref(false)
const aiLoading = ref(false)
const error = ref('')
const jobs = ref([])
const matches = ref([])
const applications = ref([])
const cvResult = ref(null)
const hasCv = ref(false)
const candidates = ref([])
const adminDashboard = ref(null)
const aiJobs = ref([])
const toast = ref('')
const filters = ref({ q: '', location: '', skill: '', salaryMin: 0, salaryMax: 180000, workMode: '' })
const page = ref(1)
const pageSize = 20
const hasNextPage = ref(false)
const totalJobs = ref(0)
const jobLoading = ref(false)
const notifications = ref([])
const selectedApplication = ref(null)
const applicationNote = ref('')
const interviewSlotInputs = ref([''])
const selectedInterviewSlotId = ref({})
const interviewDeclineReason = ref({})
const activeCandidateTab = ref('jobs')
const activeAdminTab = ref('monitoring')
const applyJob = ref(null)
const applyFile = ref(null)
const applyLoading = ref(false)
const profileOpen = ref(false)
const profileForm = ref({})
const authMode = ref('login')
const registerForm = ref({ full_name: '', email: '', password: '', role: 'candidate' })
const companyForm = ref({ name: '', industry: '', location: '', website: '', description: '' })
const jobForm = ref({ company_id: '', title: '', category: 'Data Analyst', country: '', city: '', remote: true, schedule_type: 'Full-time', description: '', required_skills: '', salary_year_avg: '' })
const adminTables = ref({ users: [], companies: [], jobs: [], auditLogs: [] })
const powerBiReport = ref(null)
const minInterviewDateTime = computed(() => {
  const date = new Date(Date.now() + 5 * 60 * 1000)
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return localDate.toISOString().slice(0, 16)
})

const role = computed(() => authStore.user?.role || 'visitor')
const cvQuality = computed(() => cvResult.value?.cv?.quality?.quality_score || (authStore.user?.role === 'candidate' ? 88 : 0))
const appliedJobIds = computed(() => new Set(applications.value.map((item) => item.job_id)))
const salaryRangeLabel = computed(() => `${Number(filters.value.salaryMin).toLocaleString()} - ${Number(filters.value.salaryMax).toLocaleString()}`)
const pendingInterviewApplications = computed(() => applications.value.filter((application) => application.status === 'InterviewTimeProposed'))

onMounted(async () => {
  if (!authStore.token) return
  try {
    const payload = await authApi.me()
    authStore.user = payload.user
    localStorage.setItem('talentbridge_user', JSON.stringify(payload.user))
    await loadDashboard()
  } catch (err) {
    authStore.logout()
  }
})

async function login() {
  loading.value = true
  error.value = ''
  try {
    const payload = await authApi.login({ email: email.value, password: password.value })
    authStore.setSession(payload)
    await loadDashboard()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function register() {
  loading.value = true
  error.value = ''
  try {
    const payload = await authApi.register(registerForm.value)
    authStore.setSession(payload)
    await loadDashboard()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function demoLogin(selectedRole) {
  const credentials = {
    candidate: ['candidate@talentbridge.local', 'candidate123'],
    recruiter: ['recruiter@talentbridge.local', 'recruiter123'],
    admin: ['admin@talentbridge.local', 'admin123'],
  }
  ;[email.value, password.value] = credentials[selectedRole]
  await login()
}

async function loadDashboard() {
  if (!authStore.user) return
  page.value = 1
  await loadJobs(false)
  notifications.value = (await notificationsApi.list()).notifications || []
  powerBiReport.value = await adminApi.powerbi()
  if (role.value === 'candidate') {
    matches.value = (await matchingApi.candidateJobs()).matches || []
    applications.value = (await applicationsApi.mine()).applications || []
    hasCv.value = ((await cvApi.mine()).cvs || []).length > 0
  }
  if (role.value === 'recruiter') {
    candidates.value = (await candidatesApi.search()).candidates || []
    if (jobs.value[0]) matches.value = (await matchingApi.jobCandidates(jobs.value[0].id)).matches || []
    applications.value = (await applicationsApi.recruiter()).applications || []
  }
  if (role.value === 'admin') {
    adminDashboard.value = await adminApi.dashboard()
    aiJobs.value = (await adminApi.aiJobs()).ai_jobs || []
    adminTables.value = {
      users: (await adminApi.users()).users || [],
      companies: (await adminApi.companies()).companies || [],
      jobs: (await adminApi.jobs()).jobs || [],
      auditLogs: (await adminApi.auditLogs()).audit_logs || [],
    }
    matches.value = []
    applications.value = []
  }
}

async function loadJobs(append = false) {
  jobLoading.value = true
  const query = new URLSearchParams()
  if (filters.value.q) query.set('q', filters.value.q)
  if (filters.value.location) query.set('location', filters.value.location)
  if (filters.value.skill) query.set('skill', filters.value.skill)
  if (Number(filters.value.salaryMin) > Number(filters.value.salaryMax)) {
    filters.value.salaryMax = filters.value.salaryMin
  }
  query.set('salaryMin', String(filters.value.salaryMin || 0))
  query.set('salaryMax', String(filters.value.salaryMax || 180000))
  if (filters.value.workMode) query.set('work_mode', filters.value.workMode)
  query.set('page', String(page.value))
  query.set('pageSize', String(pageSize))
  const jobPayload = await jobsApi.list(query.toString())
  jobs.value = append ? [...jobs.value, ...(jobPayload.items || jobPayload.jobs || [])] : (jobPayload.items || jobPayload.jobs || [])
  hasNextPage.value = !!jobPayload.hasNextPage
  totalJobs.value = jobPayload.totalCount || jobPayload.total || jobs.value.length
  jobLoading.value = false
}

async function loadMoreJobs() {
  if (!hasNextPage.value || jobLoading.value) return
  page.value += 1
  await loadJobs(true)
}

async function uploadCv(event) {
  const file = event.target.files?.[0]
  if (!file) return
  aiLoading.value = true
  error.value = ''
  try {
    await wait(450)
    cvResult.value = await cvApi.upload(file)
    hasCv.value = true
    toast.value = 'CV analyzed successfully. You can now apply to jobs.'
    setTimeout(() => { toast.value = '' }, 3500)
  } catch (err) {
    error.value = err.message
  } finally {
    aiLoading.value = false
  }
}

async function apply(jobId) {
  applyJob.value = jobs.value.find((job) => job.id === jobId)
  applyFile.value = null
}

async function confirmApply() {
  if (!applyJob.value || !applyFile.value) {
    toast.value = 'Please choose the PDF CV you want to send for this job.'
    setTimeout(() => { toast.value = '' }, 3500)
    return
  }
  applyLoading.value = true
  try {
    const uploaded = await cvApi.upload(applyFile.value)
    await applicationsApi.apply(applyJob.value.id, uploaded.cv.id)
    applications.value = (await applicationsApi.mine()).applications || []
    jobs.value = jobs.value.map((job) => job.id === applyJob.value.id ? { ...job, has_applied: true, application_status: 'Applied' } : job)
    toast.value = `Application sent successfully for ${applyJob.value.title}.`
    applyJob.value = null
    applyFile.value = null
    setTimeout(() => { toast.value = '' }, 4500)
  } catch (err) {
    toast.value = err.message.includes('Already') ? 'You already applied to this job.' : (err.message || 'Please upload a real CV PDF before applying.')
    setTimeout(() => { toast.value = '' }, 4500)
  } finally {
    applyLoading.value = false
  }
}

async function openApplication(application) {
  if (role.value !== 'recruiter') return
  selectedApplication.value = (await applicationsApi.detail(application.id)).application
  applicationNote.value = selectedApplication.value.recruiter_note || ''
  interviewSlotInputs.value = ['', '']
}

async function updateApplicationStatus(status) {
  if (!selectedApplication.value) return
  selectedApplication.value = (await applicationsApi.updateStatus(selectedApplication.value.id, status, applicationNote.value)).application
  applications.value = (await applicationsApi.recruiter()).applications || []
  toast.value = `Application updated to ${status}`
  setTimeout(() => { toast.value = '' }, 3500)
}

async function proposeInterviewSlots() {
  if (!selectedApplication.value) return
  const slots = interviewSlotInputs.value.map((item) => item ? new Date(item).toISOString() : '').filter(Boolean)
  if (!slots.length) {
    toast.value = 'Add at least one future interview time.'
    setTimeout(() => { toast.value = '' }, 3500)
    return
  }
  try {
    selectedApplication.value = (await applicationsApi.proposeInterviewSlots(selectedApplication.value.id, slots, applicationNote.value)).application
    applications.value = (await applicationsApi.recruiter()).applications || []
    notifications.value = (await notificationsApi.list()).notifications || []
    toast.value = 'Interview slots sent to the candidate.'
  } catch (err) {
    toast.value = err.message || 'Interview slots must be valid future dates.'
  }
  setTimeout(() => { toast.value = '' }, 4500)
}

function addInterviewSlotInput() {
  interviewSlotInputs.value = [...interviewSlotInputs.value, '']
}

function removeInterviewSlotInput(index) {
  interviewSlotInputs.value = interviewSlotInputs.value.filter((_, itemIndex) => itemIndex !== index)
  if (!interviewSlotInputs.value.length) interviewSlotInputs.value = ['']
}

async function selectInterviewSlot(application) {
  const slotId = selectedInterviewSlotId.value[application.id]
  if (!slotId) {
    toast.value = 'Choose one proposed interview time first.'
    setTimeout(() => { toast.value = '' }, 3500)
    return
  }
  await applicationsApi.selectInterviewSlot(application.id, slotId)
  applications.value = (await applicationsApi.mine()).applications || []
  notifications.value = (await notificationsApi.list()).notifications || []
  toast.value = 'Interview time confirmed.'
  setTimeout(() => { toast.value = '' }, 3500)
}

async function declineInterviewSlots(application) {
  await applicationsApi.declineInterviewSlots(application.id, interviewDeclineReason.value[application.id] || '')
  applications.value = (await applicationsApi.mine()).applications || []
  notifications.value = (await notificationsApi.list()).notifications || []
  toast.value = 'Recruiter notified to propose new interview times.'
  setTimeout(() => { toast.value = '' }, 4000)
}

async function saveApplicationNote() {
  if (!selectedApplication.value) return
  selectedApplication.value = (await applicationsApi.saveNote(selectedApplication.value.id, applicationNote.value)).application
  toast.value = 'Recruiter note saved'
  setTimeout(() => { toast.value = '' }, 3000)
}

async function openProfile() {
  if (role.value === 'candidate') {
    const payload = await profilesApi.candidate()
    const profile = payload.profile || {}
    profileForm.value = {
      title: profile.title || '',
      location: profile.location || '',
      preferred_country: profile.preferred_country || '',
      preferred_roles: (profile.preferred_roles || []).join(', '),
      skills: (profile.skills || []).join(', '),
      education: (profile.education || []).join(', '),
      experience_summary: profile.experience_summary || '',
      visibility: profile.visibility !== false,
    }
  } else if (role.value === 'recruiter') {
    const payload = await profilesApi.recruiter()
    const profile = payload.profile || {}
    profileForm.value = {
      title: profile.title || '',
      phone: profile.phone || '',
      company_id: profile.company_id || '',
    }
  } else {
    profileForm.value = {
      full_name: authStore.user?.full_name || '',
      email: authStore.user?.email || '',
      role: authStore.user?.role || '',
    }
  }
  profileOpen.value = true
}

async function saveProfile() {
  if (role.value === 'candidate') {
    const payload = {
      title: profileForm.value.title,
      location: profileForm.value.location,
      preferred_country: profileForm.value.preferred_country,
      preferred_roles: splitCsv(profileForm.value.preferred_roles),
      skills: splitCsv(profileForm.value.skills),
      education: splitCsv(profileForm.value.education),
      experience_summary: profileForm.value.experience_summary,
      visibility: !!profileForm.value.visibility,
    }
    await profilesApi.updateCandidate(payload)
  } else if (role.value === 'recruiter') {
    await profilesApi.updateRecruiter({
      title: profileForm.value.title,
      phone: profileForm.value.phone,
      company_id: profileForm.value.company_id ? Number(profileForm.value.company_id) : null,
    })
  }
  toast.value = 'Profile saved successfully.'
  profileOpen.value = false
  await loadDashboard()
  setTimeout(() => { toast.value = '' }, 3500)
}

async function saveCompany() {
  const payload = await companiesApi.create(companyForm.value)
  companyForm.value = { name: '', industry: '', location: '', website: '', description: '' }
  toast.value = `Company ${payload.company.name} created.`
  await loadDashboard()
  setTimeout(() => { toast.value = '' }, 3500)
}

async function createRecruiterJob() {
  const payload = {
    ...jobForm.value,
    company_id: Number(jobForm.value.company_id),
    salary_year_avg: jobForm.value.salary_year_avg ? Number(jobForm.value.salary_year_avg) : null,
    required_skills: splitCsv(jobForm.value.required_skills),
  }
  const created = await jobsApi.create(payload)
  await jobsApi.publish(created.job.id)
  jobForm.value = { company_id: '', title: '', category: 'Data Analyst', country: '', city: '', remote: true, schedule_type: 'Full-time', description: '', required_skills: '', salary_year_avg: '' }
  toast.value = 'Job created and published.'
  await loadDashboard()
  setTimeout(() => { toast.value = '' }, 3500)
}

async function closeRecruiterJob(jobId) {
  await jobsApi.close(jobId)
  toast.value = 'Job closed.'
  await loadDashboard()
  setTimeout(() => { toast.value = '' }, 3500)
}

async function markNotificationRead(notificationId) {
  await notificationsApi.markRead(notificationId)
  notifications.value = (await notificationsApi.list()).notifications || []
}

async function retryAiJob(id) {
  await adminApi.retryAiJob(id)
  aiJobs.value = (await adminApi.aiJobs()).ai_jobs || []
}

async function resetDemoData() {
  if (!confirm('Reset demo data? This clears applications, CVs, notifications, shortlists, audit logs, and custom users/jobs.')) return
  await adminApi.resetDemoData()
  toast.value = 'Demo data reset. Applications list is clean.'
  await loadDashboard()
  setTimeout(() => { toast.value = '' }, 4000)
}

function splitCsv(value) {
  return String(value || '').split(',').map((item) => item.trim()).filter(Boolean)
}

function formatStatus(value) {
  const labels = {
    Applied: 'Applied',
    UnderReview: 'Under Review',
    InterviewRequested: 'Interview Requested',
    InterviewTimeProposed: 'Choose Interview Time',
    InterviewSlotsDeclined: 'Waiting New Interview Times',
    Accepted: 'Accepted',
    Rejected: 'Rejected',
    shortlisted: 'Shortlisted',
    submitted: 'Applied',
  }
  return labels[value] || String(value || '-').replace(/([a-z])([A-Z])/g, '$1 $2')
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function openPowerBiReport() {
  if (powerBiReport.value?.report_path) window.open(`file:///${powerBiReport.value.report_path.replace(/\\/g, '/')}`, '_blank')
}

function openPowerBiLink(link) {
  if (link?.url) window.open(link.url, '_blank')
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function updateSalaryMin(value) {
  const next = Math.max(0, Number(value || 0))
  filters.value.salaryMin = Math.min(next, Number(filters.value.salaryMax))
}

function updateSalaryMax(value) {
  const next = Math.max(0, Number(value || 0))
  filters.value.salaryMax = Math.max(next, Number(filters.value.salaryMin))
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function logout() {
  authStore.logout()
  jobs.value = []
  matches.value = []
  applications.value = []
  candidates.value = []
  adminDashboard.value = null
  cvResult.value = null
}
</script>

<template>
  <main class="app-shell">
    <section class="hero-section">
      <div>
        <p class="eyebrow">AI recruitment operating system</p>
        <h1>Talent Bridge</h1>
        <p class="hero-copy">A role-based platform where candidates improve CVs, recruiters discover stronger talent, and admins monitor the AI recruitment engine.</p>
      </div>
      <aside class="panel hero-status">
        <span class="status-dot"></span>
        <strong>{{ authStore.user ? `${authStore.user.role} workspace` : 'Choose your workspace' }}</strong>
        <small v-if="authStore.user">{{ authStore.user.full_name }} · {{ authStore.user.email }}</small>
        <small v-else>Use one of the demo accounts to open a realistic workflow.</small>
      </aside>
    </section>

    <section v-if="!authStore.user" class="workspace-grid">
      <form class="panel" @submit.prevent="authMode === 'login' ? login() : register()">
        <div class="panel-heading"><span>Auth</span><h2>{{ authMode === 'login' ? 'Sign in' : 'Create account' }}</h2></div>
        <div class="tab-switcher compact-tabs">
          <button type="button" :class="authMode === 'login' ? '' : 'secondary'" @click="authMode = 'login'">Login</button>
          <button type="button" :class="authMode === 'register' ? '' : 'secondary'" @click="authMode = 'register'">Register</button>
        </div>
        <template v-if="authMode === 'login'">
          <label>Email<input v-model="email" /></label>
          <label>Password<input v-model="password" type="password" /></label>
        </template>
        <template v-else>
          <label>Full name<input v-model="registerForm.full_name" /></label>
          <label>Email<input v-model="registerForm.email" /></label>
          <label>Password<input v-model="registerForm.password" type="password" /></label>
          <label>Role<select v-model="registerForm.role"><option value="candidate">Candidate</option><option value="recruiter">Recruiter</option></select></label>
        </template>
        <button :disabled="loading">{{ authMode === 'login' ? 'Login' : 'Create account' }}</button>
        <p v-if="error" class="error-banner">{{ error }}</p>
      </form>
      <aside class="panel role-picker">
        <div class="panel-heading"><span>Demo</span><h2>Role shortcuts</h2></div>
        <button type="button" @click="demoLogin('candidate')">Candidate: improve my profile</button>
        <button type="button" class="secondary spaced" @click="demoLogin('recruiter')">Recruiter: find best candidates</button>
        <button type="button" class="secondary spaced" @click="demoLogin('admin')">Admin: monitor platform</button>
      </aside>
    </section>

    <section v-else class="result-stack">
      <nav class="role-nav panel">
        <strong>{{ role }} workspace</strong>
        <span>Dashboard</span>
        <span v-if="role === 'candidate'">CV optimization</span>
        <span v-if="role === 'candidate'">Job discovery</span>
        <span v-if="role === 'recruiter'">Candidate intelligence</span>
        <span v-if="role === 'recruiter'">Pipeline</span>
        <span v-if="role === 'admin'">AI monitoring</span>
        <details class="account-menu dropdown-menu">
          <summary>{{ authStore.user.full_name }}</summary>
          <button class="secondary" type="button" @click="openProfile">Profile</button>
          <button class="secondary" type="button" @click="logout">Logout</button>
        </details>
      </nav>

      <section v-if="role === 'candidate'" class="result-stack">
        <section class="metric-grid">
          <div class="metric-card"><small>Available Jobs</small><strong>{{ totalJobs }}</strong><span>{{ jobs.length }} loaded</span></div>
          <div class="metric-card"><small>Recommended Jobs</small><strong>{{ matches.length }}</strong><span>AI-ranked for your CV</span></div>
          <div class="metric-card"><small>Applications</small><strong>{{ applications.length }}</strong><span>tracked statuses</span></div>
          <div class="metric-card"><small>CV Quality</small><strong>{{ cvQuality }}</strong><span>profile readiness</span></div>
          <div class="metric-card"><small>Notifications</small><strong>{{ notifications.length }}</strong><span>application updates</span></div>
        </section>

        <section class="panel powerbi-launcher"><div class="panel-heading no-margin"><span>Power BI</span><h2>Candidate KPI</h2></div><p class="muted">Open the candidate-only Power BI report in a new tab. This role receives only the candidate dashboard link.</p><button v-for="link in powerBiReport?.links || []" :key="link.role" type="button" @click="openPowerBiLink(link)">{{ link.title }}</button></section>

        <section v-if="pendingInterviewApplications.length" class="panel interview-focus-panel">
          <div class="panel-heading"><span>Interview</span><h2>Choose your interview time</h2></div>
          <article v-for="application in pendingInterviewApplications" :key="`pending-interview-${application.id}`" class="match-card">
            <small>{{ application.company }} · {{ application.job_title }}</small>
            <h3>You have been selected</h3>
            <p class="muted">The recruiter proposed these times. Choose one that fits you, or ask for new slots.</p>
            <div class="slot-grid">
              <label v-for="slot in application.interview_slots" :key="slot.id" class="slot-option" :class="selectedInterviewSlotId[application.id] === slot.id ? 'selected' : ''"><input v-model="selectedInterviewSlotId[application.id]" type="radio" :value="slot.id" /><span class="slot-calendar"><strong>{{ new Date(slot.start_at).toLocaleDateString(undefined, { day: '2-digit' }) }}</strong><small>{{ new Date(slot.start_at).toLocaleDateString(undefined, { month: 'short' }) }}</small></span><span><strong>{{ new Date(slot.start_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) }}</strong><small>{{ new Date(slot.start_at).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric' }) }}</small></span></label>
            </div>
            <button class="confirm-slot-button" type="button" @click="selectInterviewSlot(application)">Confirm selected time</button>
            <label class="spaced">If none fit, explain why<textarea v-model="interviewDeclineReason[application.id]" placeholder="Example: I am only available after 17:00 this week."></textarea></label>
            <button class="secondary" type="button" @click="declineInterviewSlots(application)">These times do not fit</button>
          </article>
        </section>

        <div class="tab-switcher panel">
          <button type="button" :class="activeCandidateTab === 'jobs' ? '' : 'secondary'" @click="activeCandidateTab = 'jobs'">Looking for Job</button>
          <button type="button" :class="activeCandidateTab === 'cv' ? '' : 'secondary'" @click="activeCandidateTab = 'cv'">Enhance CV</button>
        </div>

        <section v-if="activeCandidateTab === 'cv'" class="content-grid">
          <div class="panel cv-command">
            <div class="panel-heading"><span>CV AI</span><h2>Optimization Studio</h2></div>
            <p class="muted">Upload your CV. Talent Bridge extracts skills, analyzes structure, scores quality, and recommends better job targets.</p>
            <p v-if="!hasCv" class="warning-banner">Upload and analyze your CV before applying. Applications are locked until your CV is ready.</p>
            <label>Upload CV PDF<input type="file" accept="application/pdf" @change="uploadCv" /></label>
            <div v-if="aiLoading" class="ai-steps">
              <span>Extracting skills...</span><span>Analyzing experience...</span><span>Scoring CV quality...</span><span>Generating recommendations...</span>
            </div>
            <template v-if="cvResult?.cv?.quality">
              <div class="quality-score" :class="cvResult.cv.quality.quality_label === 'Pro' ? 'success' : 'danger'"><strong>{{ cvResult.cv.quality.quality_grade || cvResult.cv.quality.quality_label }}</strong><span>{{ cvResult.cv.quality.quality_score }} / 100 · {{ cvResult.cv.quality.quality_label }}</span></div>
              <div class="extraction-grid">
                <article><small>Detected skills</small><strong>{{ cvResult.cv.extraction.detected_skills?.length || 0 }}</strong><p>{{ (cvResult.cv.extraction.detected_skills || []).join(', ') || 'No skills detected' }}</p></article>
                <article><small>Experience</small><p>{{ cvResult.cv.extraction.experience }}</p></article>
                <article><small>Education</small><p>{{ cvResult.cv.extraction.education }}</p></article>
                <article><small>Languages</small><p>{{ cvResult.cv.extraction.languages }}</p></article>
                <article><small>Certifications</small><p>{{ cvResult.cv.extraction.certifications }}</p></article>
              </div>
              <details class="cv-preview">
                <summary>Preview extracted CV text</summary>
                <p>{{ cvResult.cv.extraction.raw_text_preview }}</p>
              </details>
              <ul class="feedback-list"><li v-for="item in cvResult.cv.quality.suggestions" :key="item">{{ item }}</li></ul>
            </template>
          </div>

        </section>

        <section v-if="activeCandidateTab === 'jobs'" class="content-grid wide-left">
          <div class="panel">
            <div class="panel-heading"><span>Jobs</span><h2>Recommended Marketplace</h2></div>
            <div class="filter-grid inline-filters">
              <label>Keyword<input v-model="filters.q" placeholder="data analyst" /></label>
              <label>Location<input v-model="filters.location" placeholder="France" /></label>
              <label>Skill<input v-model="filters.skill" placeholder="sql" /></label>
              <label>Work mode<select v-model="filters.workMode"><option value="">Any</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="onsite">Onsite</option></select></label>
            </div>
            <div class="salary-filter panel compact-panel">
              <div class="salary-label"><strong>Salary range</strong><span>{{ salaryRangeLabel }}</span></div>
              <div class="salary-number-row">
                <label>Min salary<input :value="filters.salaryMin" type="number" min="0" :max="filters.salaryMax" step="5000" @input="updateSalaryMin($event.target.value)" /></label>
                <label>Max salary<input :value="filters.salaryMax" type="number" :min="filters.salaryMin" max="220000" step="5000" @input="updateSalaryMax($event.target.value)" /></label>
              </div>
            </div>
            <button class="secondary filter-action" type="button" @click="loadDashboard">Apply filters</button>
            <article v-for="job in jobs" :key="job.id" class="match-card job-card-rich">
              <div class="match-header"><div><small>{{ job.category }} · {{ job.schedule_type }} · {{ job.work_mode }}</small><h3>{{ job.title }}</h3><p>{{ job.description }}</p></div><strong>{{ job.salary_year_avg ? `${Math.round(job.salary_year_avg / 1000)}k` : '-' }}</strong></div>
              <div class="chips"><span v-for="skill in job.required_skills" :key="skill" class="chip">{{ skill }}</span></div>
              <div class="mini-metrics"><span>Class {{ job.classification?.remote_class }}</span><span>Segment {{ job.segmentation?.segment_name }}</span><span>Salary {{ job.estimated_salary_range?.[0] }}-{{ job.estimated_salary_range?.[1] }}</span></div>
              <button class="secondary" type="button" :disabled="appliedJobIds.has(job.id) || job.has_applied" @click="apply(job.id)">{{ appliedJobIds.has(job.id) || job.has_applied ? 'Applied' : 'Apply with CV' }}</button>
            </article>
            <div v-if="jobLoading" class="skeleton-list"><span></span><span></span><span></span></div>
            <p v-if="!jobs.length && !jobLoading" class="empty-state">No jobs match your filters. Try a broader keyword or remove salary/location filters.</p>
            <button v-if="hasNextPage" class="secondary spaced" type="button" @click="loadMoreJobs">Load more jobs</button>
          </div>
          <div class="panel">
            <div class="panel-heading"><span>Apps</span><h2>My Applications</h2></div>
            <article v-for="application in applications" :key="application.id" class="match-card">
              <div class="match-header"><div><small>{{ application.company }} · {{ formatDate(application.application_date) }}</small><h3>{{ application.job_title }}</h3><p>Current step: {{ formatStatus(application.current_step) }} <span v-if="application.recruiter_decision">· Decision: {{ formatStatus(application.recruiter_decision) }}</span></p></div><strong class="status-badge">{{ formatStatus(application.status) }}</strong></div>
              <div v-if="application.status === 'InterviewTimeProposed'" class="schedule-box"><strong>Action needed</strong><p class="muted">Choose your interview time in the highlighted Interview panel above.</p></div>
              <div v-if="application.selected_interview_slot" class="schedule-box confirmed-box"><strong>Confirmed interview</strong><p>{{ formatDateTime(application.selected_interview_slot.start_at) }}</p></div>
            </article>
            <div class="panel-heading compact-heading"><span>Notifications</span><h2>Recent Updates</h2></div>
            <article v-for="notification in notifications.slice(0, 4)" :key="notification.id" class="match-card"><small>{{ notification.type }} · {{ notification.read ? 'read' : 'new' }}</small><h3>{{ notification.title }}</h3><p class="muted">{{ notification.message }}</p><button v-if="!notification.read" class="secondary" type="button" @click="markNotificationRead(notification.id)">Mark read</button></article>
          </div>
        </section>
      </section>

      <section v-if="role === 'recruiter'" class="result-stack">
        <section class="metric-grid">
          <div class="metric-card"><small>Active Jobs</small><strong>{{ jobs.length }}</strong><span>published roles</span></div>
          <div class="metric-card"><small>Applications</small><strong>{{ applications.length }}</strong><span>received for your jobs</span></div>
          <div class="metric-card success"><small>Candidate Matches</small><strong>{{ matches.length }}</strong><span>AI-ranked talent</span></div>
          <div class="metric-card"><small>Candidate Pool</small><strong>{{ candidates.length }}</strong><span>searchable profiles</span></div>
          <div class="metric-card"><small>Notifications</small><strong>{{ notifications.length }}</strong><span>interview responses</span></div>
        </section>
        <section v-if="notifications.length" class="panel notification-strip">
          <div class="panel-heading no-margin"><span>Updates</span><h2>Recruiter Notifications</h2></div>
          <article v-for="notification in notifications.slice(0, 3)" :key="notification.id" class="match-card"><small>{{ notification.type }} · {{ notification.read ? 'read' : 'new' }}</small><h3>{{ notification.title }}</h3><p class="muted">{{ notification.message }}</p><button v-if="!notification.read" class="secondary" type="button" @click="markNotificationRead(notification.id)">Mark read</button></article>
        </section>
        <section class="panel powerbi-launcher"><div class="panel-heading no-margin"><span>Power BI</span><h2>Recruiter KPI</h2></div><p class="muted">Open the recruiter-only Power BI report in a new tab. This role receives only the recruiter dashboard link.</p><button v-for="link in powerBiReport?.links || []" :key="link.role" type="button" @click="openPowerBiLink(link)">{{ link.title }}</button></section>
        <section class="content-grid">
          <div class="panel"><div class="panel-heading"><span>Job AI</span><h2>Create Job Offer</h2></div><p class="muted">Create a role and Talent Bridge will classify, segment, and estimate salary signals.</p><div class="filter-grid"><label>Company ID<input v-model="jobForm.company_id" type="number" /></label><label>Title<input v-model="jobForm.title" /></label><label>Category<input v-model="jobForm.category" /></label><label>Country<input v-model="jobForm.country" /></label><label>City<input v-model="jobForm.city" /></label><label>Salary<input v-model="jobForm.salary_year_avg" type="number" /></label><label>Skills<input v-model="jobForm.required_skills" placeholder="python, sql" /></label><label>Description<input v-model="jobForm.description" /></label></div><button class="secondary" type="button" @click="createRecruiterJob">Create and publish job</button><div class="ai-steps"><span>Detecting required skills</span><span>Classifying job type</span><span>Segmenting role</span><span>Estimating salary</span></div></div>
          <div class="panel"><div class="panel-heading"><span>Candidates</span><h2>Candidate Search</h2></div><article v-for="candidate in candidates" :key="candidate.candidate_id" class="match-card"><div class="match-header"><div><small>{{ candidate.title }} · {{ candidate.location }}</small><h3>{{ candidate.name }}</h3><p>{{ candidate.skills?.slice(0, 5).join(', ') }}</p></div><strong>{{ candidate.cv_quality_score || '-' }}</strong></div></article></div>
        </section>
        <section class="content-grid">
          <div class="panel"><div class="panel-heading"><span>Company</span><h2>Create Company</h2></div><div class="filter-grid"><label>Name<input v-model="companyForm.name" /></label><label>Industry<input v-model="companyForm.industry" /></label><label>Location<input v-model="companyForm.location" /></label><label>Website<input v-model="companyForm.website" /></label></div><label>Description<textarea v-model="companyForm.description"></textarea></label><button class="secondary" type="button" @click="saveCompany">Save company</button></div>
          <div class="panel"><div class="panel-heading"><span>Jobs</span><h2>Manage Jobs</h2></div><article v-for="job in jobs.slice(0, 8)" :key="job.id" class="match-card"><div class="match-header"><div><small>{{ job.status }} · {{ job.category }}</small><h3>{{ job.title }}</h3><p>{{ job.country }} · {{ job.required_skills?.slice(0, 4).join(', ') }}</p></div><strong>{{ job.salary_year_avg ? `${Math.round(job.salary_year_avg / 1000)}k` : '-' }}</strong></div><button class="secondary" type="button" @click="closeRecruiterJob(job.id)">Close job</button></article></div>
        </section>
        <section class="content-grid wide-left">
          <div class="panel"><div class="panel-heading"><span>Applications</span><h2>Received Applications</h2></div><article v-for="application in applications" :key="application.id" class="match-card" @click="openApplication(application)"><div class="match-header"><div><small>{{ application.job_title }} · {{ formatDate(application.application_date) }}</small><h3>{{ application.candidate_name }}</h3><p>{{ application.main_extracted_skills?.join(', ') }} · CV {{ application.cv_processing_status }}</p></div><strong>{{ formatStatus(application.status) }}</strong></div></article></div>
          <div class="panel"><div class="panel-heading"><span>Matching</span><h2>Best Candidates For Current Job</h2></div><article v-for="match in matches" :key="match.candidate_id" class="match-card"><div class="match-header"><div><small>Candidate recommendation</small><h3>{{ match.candidate_name }}</h3><p>{{ (match.explanation || []).slice(0, 3).join(' · ') }}</p></div><strong>{{ match.match_score }}</strong></div></article></div>
        </section>
      </section>

      <section v-if="role === 'admin'" class="result-stack">
        <section class="metric-grid">
          <div class="metric-card"><small>Total Users</small><strong>{{ adminDashboard?.users || 0 }}</strong><span>platform accounts</span></div>
          <div class="metric-card"><small>Candidates</small><strong>{{ adminDashboard?.candidates || 0 }}</strong><span>candidate profiles</span></div>
          <div class="metric-card"><small>Recruiters</small><strong>{{ adminDashboard?.recruiters || 0 }}</strong><span>company users</span></div>
          <div class="metric-card"><small>Jobs</small><strong>{{ adminDashboard?.jobs || 0 }}</strong><span>platform jobs</span></div>
          <div class="metric-card danger"><small>Failed AI Jobs</small><strong>{{ adminDashboard?.failed_ai_jobs || 0 }}</strong><span>need review</span></div>
        </section>

        <div class="tab-switcher panel">
          <button type="button" :class="activeAdminTab === 'monitoring' ? '' : 'secondary'" @click="activeAdminTab = 'monitoring'">AI Monitoring</button>
          <button type="button" :class="activeAdminTab === 'powerbi' ? '' : 'secondary'" @click="activeAdminTab = 'powerbi'">Power BI KPI</button>
          <button type="button" :class="activeAdminTab === 'management' ? '' : 'secondary'" @click="activeAdminTab = 'management'">Data Management</button>
          <button type="button" :class="activeAdminTab === 'audit' ? '' : 'secondary'" @click="activeAdminTab = 'audit'">Audit & Retry</button>
        </div>

        <section v-if="activeAdminTab === 'monitoring'" class="content-grid">
          <div class="panel"><div class="panel-heading"><span>AI Ops</span><h2>Processing Monitor</h2></div><article v-for="job in aiJobs" :key="job.id" class="match-card"><div class="match-header"><div><small>{{ job.type }} · {{ job.status }}</small><h3>{{ job.entity || 'AI job' }}</h3><p>{{ job.error || `${job.duration_ms || 0} ms processing time` }}</p></div><strong>{{ job.status === 'failed' ? '!' : 'OK' }}</strong></div></article></div>
          <div class="panel"><div class="panel-heading"><span>Control</span><h2>Platform Supervision</h2></div><p class="muted">Monitor CV extraction, matching, recommendations, salary estimation, audit events, and failed processing jobs from one admin workspace.</p><div class="ai-steps"><span>CV extraction health</span><span>Matching engine health</span><span>Recommendation queue</span><span>Audit log review</span></div></div>
        </section>

        <section v-if="activeAdminTab === 'powerbi'" class="content-grid wide-left">
          <div class="panel powerbi-panel">
            <div class="panel-heading"><span>Power BI</span><h2>{{ powerBiReport?.title || 'Project KPI Dashboard' }}</h2></div>
            <div class="powerbi-link-grid">
              <article v-for="link in powerBiReport?.links || []" :key="link.role" class="match-card"><small>{{ link.role }} access</small><h3>{{ link.title }}</h3><p class="muted">{{ link.description }}</p><button class="secondary" type="button" @click="openPowerBiLink(link)">Open Power BI dashboard</button></article>
            </div>
            <div class="empty-state spaced">
              <strong>Existing report detected: {{ powerBiReport?.report_exists ? 'yes' : 'no' }}</strong>
              <p>{{ powerBiReport?.message }}</p>
              <p class="muted">Report file: {{ powerBiReport?.report_path }}</p>
              <button class="secondary" type="button" :disabled="!powerBiReport?.report_exists" @click="openPowerBiReport">Open existing PBIX report</button>
            </div>
          </div>
          <div class="panel"><div class="panel-heading"><span>Scope</span><h2>Role links</h2></div><p class="muted">The app only opens role-specific Power BI reports. It does not mount Power BI inside the app or rely on Azure Embedded configuration.</p><p class="warning-banner">For real separation, publish separate Candidate, Recruiter, and Admin reports, then configure the three role URLs.</p></div>
        </section>

        <section v-if="activeAdminTab === 'management'" class="content-grid">
          <div class="panel"><div class="panel-heading"><span>Users</span><h2>User Management</h2></div><article v-for="user in adminTables.users.slice(0, 8)" :key="user.id" class="match-card"><small>{{ user.role }} · {{ user.status }}</small><h3>{{ user.full_name }}</h3><p class="muted">{{ user.email }}</p></article></div>
          <div class="panel"><div class="panel-heading"><span>Companies & Jobs</span><h2>Data Management</h2></div><article v-for="company in adminTables.companies.slice(0, 4)" :key="company.id" class="match-card"><small>{{ company.industry }}</small><h3>{{ company.name }}</h3><p class="muted">{{ company.location }}</p></article><article v-for="job in adminTables.jobs.slice(0, 4)" :key="`admin-job-${job.id}`" class="match-card"><small>{{ job.status }} · {{ job.category }}</small><h3>{{ job.title }}</h3><p class="muted">{{ job.country }}</p></article></div>
        </section>

        <section v-if="activeAdminTab === 'audit'" class="content-grid">
          <div class="panel"><div class="panel-heading"><span>Audit</span><h2>Audit Logs</h2></div><article v-for="log in adminTables.auditLogs.slice(-10)" :key="log.id" class="match-card"><small>{{ log.entity_type }} #{{ log.entity_id }}</small><h3>{{ log.action }}</h3><p class="muted">{{ formatDate(log.created_at) }}</p></article></div>
          <div class="panel"><div class="panel-heading"><span>Recovery</span><h2>Failed AI Jobs</h2></div><button class="secondary spaced reset-button" type="button" @click="resetDemoData">Reset demo data</button><article v-for="job in aiJobs.filter(item => item.status === 'failed')" :key="`failed-${job.id}`" class="match-card"><small>{{ job.status }}</small><h3>{{ job.type }}</h3><p class="muted">{{ job.error }}</p><button class="secondary spaced" type="button" @click="retryAiJob(job.id)">Retry job</button></article></div>
        </section>
      </section>

      <p v-if="error" class="error-banner">{{ error }}</p>
      <p v-if="toast" class="success-banner floating-toast">{{ toast }}</p>

      <div v-if="applyJob" class="drawer-backdrop" @click.self="applyJob = null">
        <aside class="application-modal apply-modal">
          <button class="drawer-close" type="button" @click="applyJob = null">Close</button>
          <small>Apply with CV</small>
          <h2>{{ applyJob.title }}</h2>
          <p class="muted">Choose the PDF CV you want to send for this specific job. This can be different from the CV used in Enhance CV.</p>
          <label>PDF CV for this application<input type="file" accept="application/pdf" @change="applyFile = $event.target.files?.[0]" /></label>
          <div v-if="applyLoading" class="ai-steps"><span>Uploading selected CV...</span><span>Extracting application CV...</span><span>Creating application...</span></div>
          <button class="submit-application-button" type="button" :disabled="applyLoading" @click="confirmApply">Send application</button>
        </aside>
      </div>

      <div v-if="profileOpen" class="drawer-backdrop" @click.self="profileOpen = false">
        <aside class="application-modal apply-modal">
          <button class="drawer-close" type="button" @click="profileOpen = false">Close</button>
          <small>Profile</small>
          <h2>{{ role }} profile</h2>

          <template v-if="role === 'candidate'">
            <label>Title<input v-model="profileForm.title" /></label>
            <label>Location<input v-model="profileForm.location" /></label>
            <label>Preferred country<input v-model="profileForm.preferred_country" /></label>
            <label>Preferred roles<input v-model="profileForm.preferred_roles" placeholder="Data Analyst, Business Analyst" /></label>
            <label>Skills<input v-model="profileForm.skills" placeholder="python, sql, power bi" /></label>
            <label>Education<input v-model="profileForm.education" /></label>
            <label>Experience summary<textarea v-model="profileForm.experience_summary"></textarea></label>
          </template>

          <template v-else-if="role === 'recruiter'">
            <label>Title<input v-model="profileForm.title" /></label>
            <label>Phone<input v-model="profileForm.phone" /></label>
            <label>Company ID<input v-model="profileForm.company_id" type="number" /></label>
          </template>

          <template v-else>
            <label>Name<input v-model="profileForm.full_name" disabled /></label>
            <label>Email<input v-model="profileForm.email" disabled /></label>
            <label>Role<input v-model="profileForm.role" disabled /></label>
          </template>

          <button v-if="role !== 'admin'" type="button" @click="saveProfile">Save profile</button>
        </aside>
      </div>

      <div v-if="selectedApplication" class="drawer-backdrop" @click.self="selectedApplication = null">
        <aside class="application-modal">
          <button class="drawer-close" type="button" @click="selectedApplication = null">Close</button>
          <div class="modal-grid">
            <section>
              <small>CV Preview</small>
              <h2>{{ selectedApplication.candidate_name }}</h2>
              <p class="muted">{{ selectedApplication.candidate_email }}</p>
              <object v-if="selectedApplication.cv?.preview_data_url" class="pdf-preview" :data="selectedApplication.cv.preview_data_url" type="application/pdf"><p>PDF preview unavailable. {{ selectedApplication.cv?.file_name }}</p></object>
              <div v-else class="cv-preview modal-preview"><strong>{{ selectedApplication.cv?.file_name }}</strong><p>{{ selectedApplication.cv?.extraction?.raw_text_preview || selectedApplication.cv?.extraction?.summary || 'No CV file uploaded yet. Showing profile-derived extraction.' }}</p></div>
              <textarea v-model="applicationNote" placeholder="Recruiter notes"></textarea>
              <button class="secondary spaced" type="button" @click="saveApplicationNote">Save note</button>
            </section>
            <section>
              <small>NER Extraction & Match</small>
              <h2>Candidate Intelligence</h2>
              <div class="extraction-grid">
                <article><small>Skills</small><p>{{ selectedApplication.cv?.extraction?.skills?.join(', ') || selectedApplication.main_extracted_skills?.join(', ') }}</p></article>
                <article><small>Experience</small><p>{{ selectedApplication.cv?.extraction?.experience }}</p></article>
                <article><small>Education</small><p>{{ Array.isArray(selectedApplication.cv?.extraction?.education) ? selectedApplication.cv.extraction.education.join(', ') : selectedApplication.cv?.extraction?.education }}</p></article>
                <article><small>Languages</small><p>{{ Array.isArray(selectedApplication.cv?.extraction?.languages) ? selectedApplication.cv.extraction.languages.join(', ') : selectedApplication.cv?.extraction?.languages }}</p></article>
                <article><small>Certifications</small><p>{{ Array.isArray(selectedApplication.cv?.extraction?.certifications) ? selectedApplication.cv.extraction.certifications.join(', ') : selectedApplication.cv?.extraction?.certifications }}</p></article>
                <article><small>Match score</small><strong>{{ selectedApplication.matching?.score }}</strong><p>{{ selectedApplication.matching?.explanation?.join(' · ') }}</p></article>
              </div>
              <div class="schedule-box">
                <strong>Propose interview times</strong>
                <p class="muted">Add one or multiple future slots. The candidate will receive a notification and choose the best time.</p>
                <div class="slot-input-grid">
                  <label v-for="(_, index) in interviewSlotInputs" :key="`slot-input-${index}`" class="datetime-card"><span>Interview slot {{ index + 1 }}</span><input v-model="interviewSlotInputs[index]" type="datetime-local" :min="minInterviewDateTime" /><button v-if="interviewSlotInputs.length > 1" class="secondary compact-button" type="button" @click="removeInterviewSlotInput(index)">Remove slot</button></label>
                </div>
                <button class="secondary" type="button" @click="addInterviewSlotInput">Add another slot</button>
                <button class="spaced" type="button" @click="proposeInterviewSlots">Send slots to candidate</button>
                <p v-if="selectedApplication.interview_status" class="muted spaced">{{ selectedApplication.interview_status }}</p>
                <p v-if="selectedApplication.interview_decline_reason" class="warning-banner">Candidate declined previous slots: {{ selectedApplication.interview_decline_reason }}</p>
                <div v-if="selectedApplication.selected_interview_slot" class="confirmed-box"><strong>Confirmed slot</strong><p>{{ formatDateTime(selectedApplication.selected_interview_slot.start_at) }}</p></div>
              </div>
              <button class="secondary spaced" type="button" @click="updateApplicationStatus('Rejected')">Reject</button>
            </section>
          </div>
        </aside>
      </div>
    </section>
  </main>
</template>
