<template>
  <div class="dashboard">
    <header class="topbar">
      <ThemeToggle />
      <router-link v-if="user?.role === 'manager'" to="/manager" class="mgr-link">Valdymas</router-link>
      <button class="app-name" @click="activeTab = 'home'">Darbuotojų Apskaita</button>
      <div class="user-area">
        <button class="username-btn" @click="activeTab = 'profile'">{{ user?.first_name }} {{ user?.last_name }}</button>
        <button class="logout-btn" @click="logout">Atsijungti</button>
      </div>
    </header>

    <main class="content">

      <!-- ── Home ── -->
      <template v-if="activeTab === 'home'">
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-value">{{ monthHours.toFixed(1) }}</div>
            <div class="stat-label">val. šį mėnesį</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ weekHours.toFixed(1) }}</div>
            <div class="stat-label">val. šią savaitę</div>
          </div>
        </div>

        <div class="quick-nav">
          <button class="quick-card" @click="activeTab = 'hours'">
            <span class="qc-icon">⏱</span>
            <span class="qc-label">Įvesti valandas</span>
            <span class="qc-sub">Pridėti darbo laiko įrašą</span>
          </button>
          <button class="quick-card" @click="activeTab = 'history'">
            <span class="qc-icon">📅</span>
            <span class="qc-label">Valandų istorija</span>
            <span class="qc-sub">Visi darbo laiko įrašai</span>
          </button>
          <button class="quick-card" @click="activeTab = 'vacation'">
            <span class="qc-icon">🏖️</span>
            <span class="qc-label">Atostogos</span>
            <span class="qc-sub">Atostogų prašymas</span>
            <span v-if="pendingVacation" class="qc-badge">{{ pendingVacation }}</span>
          </button>
          <button class="quick-card" @click="activeTab = 'sick'">
            <span class="qc-icon">🤒</span>
            <span class="qc-label">Nedarbingumas</span>
            <span class="qc-sub">Pranešimas apie ligą</span>
            <span v-if="pendingSick" class="qc-badge">{{ pendingSick }}</span>
          </button>
          <button class="quick-card" @click="activeTab = 'projects'">
            <span class="qc-icon">📌</span>
            <span class="qc-label">Projektai</span>
            <span class="qc-sub">Aktyvių projektų sąrašas</span>
          </button>
          <button class="quick-card" @click="activeTab = 'profile'">
            <span class="qc-icon">👤</span>
            <span class="qc-label">Profilis</span>
            <span class="qc-sub">El. paštas ir slaptažodis</span>
            <span v-if="!user?.email" class="qc-badge qc-badge-warn">!</span>
          </button>
        </div>
      </template>

      <!-- ── Įvesti valandas ── -->
      <template v-else-if="activeTab === 'hours'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <HoursForm :editEntry="null" @logged="onHoursLogged" />
      </template>

      <!-- ── Valandų istorija ── -->
      <template v-else-if="activeTab === 'history'">
        <button class="back-btn" @click="cancelEdit">← Atgal</button>
        <HoursForm v-if="editingEntry" :editEntry="editingEntry" @logged="onEditSaved" @cancel="cancelEdit" />
        <LogHistory title="Darbo valandų istorija" :entries="hours" type="hours" @deleted="refreshHours" @edit="startEdit" />
      </template>

      <!-- ── Atostogos ── -->
      <template v-else-if="activeTab === 'vacation'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <LeaveRequestForm type="vacation" @submitted="refreshLeave" />
        <LeaveRequestList title="Mano atostogų prašymai" :entries="vacationRequests" @cancelled="refreshLeave" />
      </template>

      <!-- ── Nedarbingumas ── -->
      <template v-else-if="activeTab === 'sick'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <LeaveRequestForm type="sick" @submitted="refreshLeave" />
        <LeaveRequestList title="Mano nedarbingumo prašymai" :entries="sickRequests" @cancelled="refreshLeave" />
      </template>

      <!-- ── Projektai ir užduotys (peržiūra) ── -->
      <template v-else-if="activeTab === 'projects'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <div class="section-header"><h2>Projektai ir jų užduotys</h2></div>
        <div v-if="projectsLoading" class="loading">Kraunama…</div>
        <div v-else>
          <p v-if="!projects.length" class="empty">Projektų dar nėra.</p>
          <ul v-else class="project-list">
            <li v-for="p in projects" :key="p.id" class="project-card">
              <span class="project-name">{{ p.name }}</span>
              <span v-if="p.address" class="project-address">📍 {{ p.address }}</span>
              <span v-else-if="p.latitude != null" class="project-address">
                📍 {{ p.latitude.toFixed(5) }}, {{ p.longitude.toFixed(5) }}
              </span>
              <div v-if="(projectTasksMap[p.id] || []).length" style="margin-top:8px; padding-top:8px; border-top:1px solid var(--border);">
                <div style="font-size:12px; font-weight:600; color:var(--text); margin-bottom:4px;">Priskirtos užduotys:</div>
                <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:4px;">
                  <li v-for="t in projectTasksMap[p.id]" :key="t.id" style="font-size:13px; color:var(--text-h);">
                    • <strong>{{ t.title }}</strong>
                    <span v-if="t.description" style="color:var(--text); font-size:12px;"> — {{ t.description }}</span>
                  </li>
                </ul>
              </div>
            </li>
          </ul>
        </div>
      </template>

      <!-- ── Profilis ── -->
      <template v-else-if="activeTab === 'profile'">
        <button class="back-btn" @click="activeTab = 'home'">← Atgal</button>
        <div class="section-header"><h2>Mano profilis</h2></div>

        <div class="profile-card">
          <p v-if="!user?.email" class="profile-warn">
            Jūsų paskyra neturi el. pašto — negalėsite atkurti slaptažodžio. Nustatykite jį žemiau.
          </p>

          <form @submit.prevent="saveProfile" class="profile-form">
            <div class="field">
              <label>El. paštas</label>
              <input v-model="profileEmail" type="email" placeholder="jusu@pastas.lt" />
            </div>
            <div class="field">
              <label>Vardas</label>
              <input v-model="profileFirst" type="text" />
            </div>
            <div class="field">
              <label>Pavardė</label>
              <input v-model="profileLast" type="text" />
            </div>
            <p v-if="profileMsg" class="profile-success">{{ profileMsg }}</p>
            <p v-if="profileError" class="error">{{ profileError }}</p>
            <button type="submit" :disabled="profileSaving">
              {{ profileSaving ? 'Saugoma…' : 'Išsaugoti' }}
            </button>
          </form>
        </div>

        <div class="profile-card" style="margin-top:16px">
          <h3>Keisti slaptažodį</h3>
          <form @submit.prevent="changePassword" class="profile-form">
            <div class="field">
              <label>Dabartinis slaptažodis</label>
              <input v-model="pwCurrent" type="password" autocomplete="current-password" />
            </div>
            <div class="field">
              <label>Naujas slaptažodis</label>
              <input v-model="pwNew" type="password" autocomplete="new-password" />
            </div>
            <p v-if="pwMsg" class="profile-success">{{ pwMsg }}</p>
            <p v-if="pwError" class="error">{{ pwError }}</p>
            <button type="submit" :disabled="pwSaving">
              {{ pwSaving ? 'Keičiama…' : 'Keisti slaptažodį' }}
            </button>
          </form>
        </div>
      </template>

    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuth } from '../composables/useAuth'
import ThemeToggle from '../components/ThemeToggle.vue'
import HoursForm from '../components/HoursForm.vue'
import LogHistory from '../components/LogHistory.vue'
import LeaveRequestForm from '../components/LeaveRequestForm.vue'
import LeaveRequestList from '../components/LeaveRequestList.vue'
import API from '../api'

const { user, fetchMe, logout } = useAuth()

const activeTab = ref('home')
const hours = ref([])
const leaveRequests = ref([])
const projects = ref([])
const projectTasksMap = ref({})
const projectsLoading = ref(false)
const editingEntry = ref(null)

function startEdit(entry) {
  editingEntry.value = entry
  activeTab.value = 'history'
}

function cancelEdit() {
  editingEntry.value = null
  activeTab.value = 'home'
}

async function onEditSaved() {
  editingEntry.value = null
  await refreshHours()
}

const vacationRequests = computed(() => leaveRequests.value.filter(r => r.type === 'vacation'))
const sickRequests     = computed(() => leaveRequests.value.filter(r => r.type === 'sick'))
const pendingVacation  = computed(() => vacationRequests.value.filter(r => r.status === 'pending').length)
const pendingSick      = computed(() => sickRequests.value.filter(r => r.status === 'pending').length)

function isoWeekBounds() {
  const now = new Date()
  const day = now.getDay() === 0 ? 7 : now.getDay()
  const mon = new Date(now)
  mon.setDate(now.getDate() - (day - 1))
  mon.setHours(0, 0, 0, 0)
  const sun = new Date(mon)
  sun.setDate(mon.getDate() + 6)
  sun.setHours(23, 59, 59, 999)
  return [mon, sun]
}

const monthHours = computed(() => {
  const now = new Date()
  const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  return hours.value.filter(e => e.date.startsWith(ym)).reduce((s, e) => s + e.hours, 0)
})

const weekHours = computed(() => {
  const [mon, sun] = isoWeekBounds()
  return hours.value.filter(e => {
    const d = new Date(e.date)
    return d >= mon && d <= sun
  }).reduce((s, e) => s + e.hours, 0)
})

async function refreshHours() {
  const params = user.value?.id ? { user_id: user.value.id } : {}
  const res = await API.get('/hours', { params })
  hours.value = res.data
}

async function onHoursLogged() {
  await refreshHours()
  activeTab.value = 'home'
}

async function refreshLeave() {
  const res = await API.get('/leave', { params: { user_id: user.value?.id } })
  leaveRequests.value = res.data
}

async function loadProjects() {
  projectsLoading.value = true
  const res = await API.get('/projects')
  const active = res.data.filter(p => !p.is_completed)
  projects.value = active
  const map = {}
  await Promise.all(active.map(async (p) => {
    try {
      const tRes = await API.get(`/projects/${p.id}/tasks`)
      map[p.id] = tRes.data
    } catch {
      map[p.id] = []
    }
  }))
  projectTasksMap.value = map
  projectsLoading.value = false
}

// ── Profile ──
const profileEmail = ref('')
const profileFirst = ref('')
const profileLast  = ref('')
const profileMsg   = ref('')
const profileError = ref('')
const profileSaving = ref(false)

const pwCurrent = ref('')
const pwNew     = ref('')
const pwMsg     = ref('')
const pwError   = ref('')
const pwSaving  = ref(false)

watch(user, (u) => {
  if (u) {
    profileEmail.value = u.email || ''
    profileFirst.value = u.first_name || ''
    profileLast.value  = u.last_name || ''
  }
}, { immediate: true })

async function saveProfile() {
  profileMsg.value   = ''
  profileError.value = ''
  profileSaving.value = true
  try {
    await API.patch('/auth/me', {
      email:      profileEmail.value,
      first_name: profileFirst.value,
      last_name:  profileLast.value,
    })
    await fetchMe()
    profileMsg.value = 'Išsaugota!'
  } catch (e) {
    profileError.value = e.response?.data?.error || 'Nepavyko išsaugoti'
  } finally {
    profileSaving.value = false
  }
}

async function changePassword() {
  pwMsg.value   = ''
  pwError.value = ''
  pwSaving.value = true
  try {
    await API.patch('/auth/me', {
      current_password: pwCurrent.value,
      password:         pwNew.value,
    })
    pwMsg.value = 'Slaptažodis pakeistas!'
    pwCurrent.value = ''
    pwNew.value = ''
  } catch (e) {
    pwError.value = e.response?.data?.error || 'Nepavyko pakeisti'
  } finally {
    pwSaving.value = false
  }
}

onMounted(async () => {
  await fetchMe()
  await Promise.all([refreshHours(), refreshLeave(), loadProjects()])
})
</script>

<style scoped>
.dashboard { min-height: 100svh; display: flex; flex-direction: column; background: var(--bg); }

/* ── Topbar ── */
.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px clamp(16px, 4vw, 28px);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  min-height: 52px;
  height: auto;
  flex-shrink: 0;
  flex-wrap: wrap;
  box-shadow: var(--shadow-sm);
}

.app-name {
  font-weight: 700;
  font-size: 15px;
  color: var(--text-h);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  flex: 1;
  min-width: 0;
  font-family: inherit;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-name:hover { color: var(--accent); }

.user-area { display: flex; align-items: center; gap: 12px; margin-left: auto; }

.username-btn {
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-family: inherit;
  display: none;
}

@media (min-width: 480px) {
  .username-btn { display: inline; }
}

.username-btn:hover { color: var(--accent); text-decoration: underline; }

.mgr-link {
  font-size: 13px;
  font-weight: 500;
  color: var(--accent);
  text-decoration: none;
  padding: 5px 12px;
  border: 1.5px solid var(--accent-border);
  border-radius: var(--radius-sm);
  background: var(--accent-bg);
  transition: background 0.15s;
}

.mgr-link:hover { background: var(--accent); color: #fff; }

.logout-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.logout-btn:hover { border-color: var(--danger); color: var(--danger); }

/* ── Content ── */
.content {
  padding: clamp(16px, 4vw, 28px);
  width: 100%;
  box-sizing: border-box;
}

/* ── Stats ── */
.stats-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }

.stat-card {
  flex: 1;
  min-width: 120px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(14px, 3vw, 22px) clamp(16px, 4vw, 24px);
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.stat-value {
  font-size: clamp(26px, 8vw, 38px);
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
  letter-spacing: -0.02em;
}

.stat-label { font-size: 12px; color: var(--text); margin-top: 6px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }

/* ── Nav cards ── */
.quick-nav {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.quick-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: clamp(14px, 4vw, 20px) clamp(12px, 4vw, 22px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
}

.quick-card:hover {
  border-color: var(--accent-border);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.qc-icon { font-size: 22px; margin-bottom: 8px; }
.qc-label { font-size: 15px; font-weight: 600; color: var(--text-h); }
.qc-sub { font-size: 12px; color: var(--text); }

.qc-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  background: var(--accent);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
}

/* ── Back button ── */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
  padding: 7px 14px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s, border-color 0.15s;
}

.back-btn:hover { color: var(--text-h); border-color: var(--text-h); }

/* ── Projects read-only list ── */
.section-header { margin-bottom: 18px; }

.loading { color: var(--text); padding: 32px 0; text-align: center; font-size: 14px; }
.empty { color: var(--text); font-size: 14px; margin: 0; }

.project-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }

.project-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.project-name { font-size: 14px; font-weight: 600; color: var(--text-h); }
.project-address { font-size: 12px; color: var(--text); }

/* ── Profile ── */
.profile-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(14px, 3vw, 22px) clamp(16px, 4vw, 24px);
  box-shadow: var(--shadow-sm);
}

.profile-card h3 { margin: 0 0 16px; font-size: 15px; color: var(--text-h); }

.profile-form { display: flex; flex-direction: column; gap: 14px; }

.profile-warn {
  font-size: 13px;
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fde68a;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin: 0 0 16px;
}

.profile-success {
  color: #166534;
  font-size: 13px;
  background: var(--success-bg);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin: 0;
}

.profile-form input {
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-h);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.profile-form input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.profile-form button[type="submit"] {
  padding: 10px;
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

.profile-form button[type="submit"]:hover { background: var(--accent-hover); }
.profile-form button:disabled { opacity: 0.55; cursor: default; }

.qc-badge-warn { background: #f59e0b; }

.error { color: var(--danger); font-size: 13px; background: var(--danger-bg); padding: 8px 12px; border-radius: var(--radius-sm); margin: 0; }
</style>
