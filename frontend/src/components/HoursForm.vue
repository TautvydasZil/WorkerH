<template>
  <TimePicker ref="timePicker" />
  <DatePicker ref="datePicker" />
  <div class="form-card">
    <h2>{{ editEntry ? 'Redaguoti įrašą' : 'Įvesti darbo valandas' }}</h2>

    <!-- ── Step 1: project selection ── -->
    <template v-if="!selectedProject && !editEntry">
      <div v-if="!projects.length" class="empty-hint">
        Vadybininkas dar nesukūrė projektų. Prašykite sukurti bent vieną.
      </div>
      <template v-else>
        <div class="search-wrap">
          <input
            v-model="search"
            type="text"
            class="search-input"
            placeholder="Ieškoti projekto…"
            autofocus
          />
        </div>
        <ul class="project-pick-list">
          <li
            v-for="p in filteredProjects"
            :key="p.id"
            class="project-pick-item"
            @click="selectProject(p)"
          >
            <span class="pick-name">{{ p.name }}</span>
            <span v-if="p.address" class="pick-addr">📍 {{ p.address }}</span>
          </li>
          <li v-if="!filteredProjects.length" class="pick-empty">Nieko nerasta.</li>
        </ul>
      </template>
    </template>

    <!-- ── Step 2: time / date form ── -->
    <template v-else>
      <!-- Selected project header -->
      <div class="selected-project">
        <span class="sel-label">Projektas:</span>
        <span class="sel-name">{{ selectedProject?.name ?? editEntry?.project_name }}</span>
        <button v-if="!editEntry" type="button" class="change-btn" @click="changeProject">Keisti</button>
      </div>

      <form @submit.prevent="submit">
        <div class="field">
          <label>Užduotis projekte</label>
          <select v-model="form.task_id" required>
            <option value="" disabled>-- Pasirinkite užduotį --</option>
            <option v-for="t in projectTasks" :key="t.id" :value="t.id">
              {{ t.title }}
            </option>
          </select>
          <span v-if="!projectTasks.length" class="optional" style="font-size:12px">
            Šiame projekte dar nėra sukurtų užduočių.
          </span>
        </div>

        <div class="field">
          <label>Data</label>
          <button type="button" class="date-btn" @click="openDatePicker">
            <svg class="date-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
            </svg>
            <span class="date-value">{{ formatDate(form.date) }}</span>
          </button>
        </div>

        <!-- Time row -->
        <div class="time-row">
          <div class="time-field">
            <label>Pradžia</label>
            <button type="button" class="time-btn" @click="openPicker('start')">{{ startTime }}</button>
          </div>
          <span class="time-sep">→</span>
          <div class="time-field">
            <label>Pabaiga</label>
            <button type="button" class="time-btn" @click="openPicker('end')">{{ endTime }}</button>
          </div>
        </div>

        <!-- Lunch break toggle -->
        <div class="lunch-row">
          <span class="lunch-label-text">Pietų pertrauka</span>
          <button type="button" class="toggle-switch" :class="{ on: lunchEnabled }" @click="lunchEnabled = !lunchEnabled" :aria-pressed="lunchEnabled">
            <span class="toggle-option left" :class="{ active: !lunchEnabled }">Ne</span>
            <span class="toggle-knob" />
            <span class="toggle-option right" :class="{ active: lunchEnabled }">Taip</span>
          </button>
        </div>
        <div v-if="lunchEnabled" class="lunch-duration-row">
          <label class="lunch-duration-label">Pertraukos trukmė</label>
          <div class="lunch-duration">
            <input
              v-model.number="form.lunch_break"
              type="number"
              min="1"
              max="480"
              class="lunch-input"
            />
            <span class="unit">min.</span>
          </div>
        </div>

        <!-- Result bar -->
        <div class="hours-display" :class="{ invalid: computedHours <= 0 }">
          <span class="hours-label">Darbo laikas:</span>
          <span class="hours-value">
            {{ computedHours > 0 ? formatHours(computedHours) : 'Netinkamas laikas' }}
          </span>
          <span v-if="lunchEnabled && form.lunch_break && computedHours > 0" class="hours-sub">
            (su {{ form.lunch_break }} min. pertrauka)
          </span>
        </div>

        <div class="field">
          <label>Pastabos <span class="optional">(neprivaloma)</span></label>
          <input v-model="form.notes" type="text" placeholder="Komentarą palikti čia..." />
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button type="submit" :disabled="loading || computedHours <= 0">
            {{ loading ? 'Saugoma…' : (editEntry ? 'Išsaugoti' : 'Įvesti valandas') }}
          </button>
          <button v-if="editEntry" type="button" class="cancel-btn" @click="emit('cancel')">Atšaukti</button>
        </div>
      </form>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import API from '../api'
import TimePicker from './TimePicker.vue'
import DatePicker from './DatePicker.vue'

const props = defineProps({ editEntry: { type: Object, default: null } })
const emit = defineEmits(['logged', 'cancel'])

const today = new Date().toISOString().split('T')[0]

const startTime = ref('08:00')
const endTime   = ref('17:00')
const timePicker = ref(null)
const datePicker = ref(null)

const monthNames = ['sausio','vasario','kovo','balandžio','gegužės','birželio','liepos','rugpjūčio','rugsėjo','spalio','lapkričio','gruodžio']

function formatDate(str) {
  if (!str) return '—'
  const d = new Date(str + 'T00:00:00')
  return `${d.getDate()} ${monthNames[d.getMonth()]} ${d.getFullYear()}`
}

async function openDatePicker() {
  const result = await datePicker.value.show(form.value.date, 'Data')
  if (result !== null) form.value.date = result
}

async function openPicker(which) {
  const current = which === 'start' ? startTime.value : endTime.value
  const label   = which === 'start' ? 'Darbo pradžia' : 'Darbo pabaiga'
  const result  = await timePicker.value.show(current, label)
  if (result !== null) {
    if (which === 'start') startTime.value = result
    else endTime.value = result
  }
}

const form = ref({ project_id: '', task_id: '', date: today, lunch_break: 60, notes: '' })
const lunchEnabled = ref(false)
const error = ref('')
const loading = ref(false)
const projects = ref([])
const projectTasks = ref([])
const selectedProject = ref(null)
const search = ref('')

const filteredProjects = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return projects.value
  return projects.value.filter(p => p.name.toLowerCase().includes(q))
})

async function fetchProjectTasks(projectId) {
  if (!projectId) {
    projectTasks.value = []
    return
  }
  try {
    const res = await API.get(`/projects/${projectId}/tasks`)
    projectTasks.value = res.data
    if (!form.value.task_id && res.data.length) {
      form.value.task_id = res.data[0].id
    }
  } catch {
    projectTasks.value = []
  }
}

async function selectProject(p) {
  selectedProject.value = p
  form.value.project_id = p.id
  form.value.task_id = ''
  await fetchProjectTasks(p.id)
}

function changeProject() {
  selectedProject.value = null
  projectTasks.value = []
  form.value.project_id = ''
  form.value.task_id = ''
  search.value = ''
}

const computedHours = computed(() => {
  if (!startTime.value || !endTime.value) return 0
  const [sh, sm] = startTime.value.split(':').map(Number)
  const [eh, em] = endTime.value.split(':').map(Number)
  const lunch = lunchEnabled.value ? (form.value.lunch_break || 0) : 0
  return (eh * 60 + em - (sh * 60 + sm) - lunch) / 60
})

function formatHours(h) {
  const totalMin = Math.round(h * 60)
  const hrs = Math.floor(totalMin / 60)
  const mins = totalMin % 60
  if (hrs === 0) return `${mins} min.`
  if (mins === 0) return `${hrs} val.`
  return `${hrs} val. ${mins} min.`
}

async function loadFromEntry(entry) {
  if (!entry) return
  form.value.project_id = entry.project_id ?? ''
  form.value.task_id = entry.task_id ?? ''
  form.value.date = entry.date
  form.value.notes = entry.notes ?? ''
  if (entry.lunch_break) {
    lunchEnabled.value = true
    form.value.lunch_break = entry.lunch_break
  } else {
    lunchEnabled.value = false
    form.value.lunch_break = 60
  }
  if (entry.start_time) startTime.value = entry.start_time
  if (entry.end_time) endTime.value = entry.end_time
  if (entry.project_id) {
    await fetchProjectTasks(entry.project_id)
    if (entry.task_id) form.value.task_id = entry.task_id
  }
}

watch(() => props.editEntry, loadFromEntry, { immediate: true })

onMounted(async () => {
  const res = await API.get('/projects')
  projects.value = res.data.filter(p => !p.is_completed)
  if (props.editEntry) {
    const allProjects = res.data
    selectedProject.value = allProjects.find(p => p.id === props.editEntry.project_id) ?? null
  }
})

function resetForm() {
  selectedProject.value = null
  projectTasks.value = []
  search.value = ''
  form.value = { project_id: '', task_id: '', date: today, lunch_break: 60, notes: '' }
  lunchEnabled.value = false
  startTime.value = '08:00'
  endTime.value = '17:00'
}

async function submit() {
  error.value = ''
  loading.value = true
  const payload = {
    project_id: form.value.project_id || null,
    task_id: form.value.task_id || null,
    date: form.value.date,
    start_time: startTime.value,
    end_time: endTime.value,
    lunch_break: lunchEnabled.value ? (form.value.lunch_break || 0) : 0,
    notes: form.value.notes
  }
  try {
    if (props.editEntry) {
      if (payload.project_id && payload.task_id) {
        await API.put(`/projects/${payload.project_id}/tasks/${payload.task_id}/hours/${props.editEntry.id}`, payload)
      } else {
        await API.put(`/hours/${props.editEntry.id}`, payload)
      }
    } else if (payload.project_id && payload.task_id) {
      await API.post(`/projects/${payload.project_id}/tasks/${payload.task_id}/hours`, payload)
    } else {
      await API.post('/hours', payload)
    }
    resetForm()
    emit('logged')
  } catch (e) {
    error.value = e.response?.data?.error || 'Nepavyko išsaugoti'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(16px, 4vw, 24px);
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

h2 { margin: 0 0 18px; font-size: 17px; }

/* ── Project search / pick ── */
.search-wrap { margin-bottom: 10px; }

.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.project-pick-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 340px;
  overflow-y: auto;
}

.project-pick-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px 14px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  background: var(--surface);
  transition: border-color 0.15s, background 0.15s;
}

.project-pick-item:hover { border-color: var(--accent-border); background: var(--accent-bg); }

.pick-name { font-size: 14px; font-weight: 600; color: var(--text-h); }
.pick-addr { font-size: 12px; color: var(--text); }
.pick-empty { font-size: 13px; color: var(--text); padding: 8px 0; }

.empty-hint { font-size: 13px; color: var(--text); font-style: italic; }

/* ── Selected project bar ── */
.selected-project {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--accent-bg);
  border: 1.5px solid var(--accent-border);
  border-radius: var(--radius-sm);
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.sel-label { font-size: 12px; color: var(--text); font-weight: 500; }
.sel-name { font-size: 14px; font-weight: 600; color: var(--accent); flex: 1; }

.change-btn {
  padding: 4px 10px;
  background: transparent;
  border: 1.5px solid var(--accent-border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--accent);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.change-btn:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

/* ── Form ── */
form { display: flex; flex-direction: column; gap: 14px; }

.field { display: flex; flex-direction: column; gap: 5px; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

.optional { font-weight: 400; color: var(--text); }

input[type="date"], input[type="text"], input[type="number"], select {
  padding: 9px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

input:focus, select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

/* ── Time row ── */
.time-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.time-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
  min-width: 110px;
}

.time-btn {
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 18px;
  font-weight: 500;
  font-family: var(--mono);
  letter-spacing: 0.06em;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.time-btn:hover {
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.time-btn:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.time-sep {
  font-size: 16px;
  color: var(--text);
  padding-bottom: 12px;
  flex-shrink: 0;
  user-select: none;
}

/* ── Date button ── */
.date-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 10px 13px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.date-btn:hover { border-color: var(--accent-border); background: var(--accent-bg); }

.date-btn:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.date-icon {
  width: 16px;
  height: 16px;
  color: var(--text);
  flex-shrink: 0;
}

.date-value { flex: 1; }

/* ── Lunch ── */
.lunch-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: var(--muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.lunch-label-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-h);
  flex: 1;
}

/* ── Toggle switch ── */
.toggle-switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 90px;
  height: 30px;
  border-radius: 99px;
  border: 1.5px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  padding: 3px;
  transition: background 0.2s, border-color 0.2s;
  flex-shrink: 0;
  font-family: inherit;
  gap: 0;
}

.toggle-switch.on {
  background: var(--accent);
  border-color: var(--accent);
}

.toggle-knob {
  position: absolute;
  left: 3px;
  width: 38px;
  height: 22px;
  border-radius: 99px;
  background: var(--border);
  transition: transform 0.22s cubic-bezier(.4,0,.2,1), background 0.2s;
  flex-shrink: 0;
  z-index: 1;
}

.toggle-switch.on .toggle-knob {
  transform: translateX(45px);
  background: rgba(255,255,255,0.35);
}

.toggle-option {
  flex: 1;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  user-select: none;
  z-index: 2;
  transition: color 0.2s;
  position: relative;
}

.toggle-option.active { color: var(--text-h); }
.toggle-switch.on .toggle-option.right { color: #fff; }
.toggle-switch.on .toggle-option.left  { color: rgba(255,255,255,0.55); }

/* ── Lunch duration row ── */
.lunch-duration-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-sm);
}

.lunch-duration-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-h);
  flex: 1;
}

.lunch-duration { display: flex; align-items: center; gap: 6px; }

.lunch-input { width: 76px; }
.unit { font-size: 13px; color: var(--text); }

/* ── Result bar ── */
.hours-display {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  background: var(--accent-bg);
  border: 1.5px solid var(--accent-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  flex-wrap: wrap;
}

.hours-display.invalid { background: var(--danger-bg); border-color: #fca5a5; }

.hours-label { color: var(--text); font-size: 13px; }
.hours-value { font-weight: 700; color: var(--accent); font-size: 16px; }
.hours-display.invalid .hours-value { color: var(--danger); }
.hours-sub { font-size: 12px; color: var(--text); }

button[type="submit"] {
  padding: 10px 22px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

button[type="submit"]:hover { background: var(--accent-hover); }
button:disabled { opacity: 0.55; cursor: default; }

.form-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.form-actions button[type="submit"],
.form-actions .cancel-btn { flex: 1; }

.cancel-btn {
  padding: 10px 18px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.cancel-btn:hover { border-color: var(--text-h); color: var(--text-h); }

.error { color: var(--danger); font-size: 13px; margin: 0; }
</style>
