<template>
  <ConfirmDialog ref="confirmDialog" />
  <div class="dashboard">
    <header class="topbar">
      <ThemeToggle />
      <span class="app-name">Darbuotojų Apskaita — Administravimas</span>
      <nav class="tabs">
        <button :class="['tab', { active: activeTab === 'invites' }]" @click="activeTab = 'invites'">Pakvietimai</button>
        <button :class="['tab', { active: activeTab === 'users' }]" @click="activeTab = 'users'">Naudotojai</button>
        <button :class="['tab', { active: activeTab === 'projects' }]" @click="activeTab = 'projects'">Projektai</button>
      </nav>
      <div class="user-area">
        <span class="username">{{ user?.first_name }} {{ user?.last_name }}</span>
        
        <button class="logout-btn" @click="logout">Atsijungti</button>
      </div>
    </header>

    <main class="content">
      <template v-if="activeTab === 'projects'">
        <ProjectsPanel />
      </template>

      <template v-else-if="activeTab === 'users'">
        <h2>Naudotojų paskyrų valdymas</h2>
        <div v-if="usersLoading" class="loading">Kraunama…</div>
        <div v-else>
          <p v-if="!users.length" class="empty">Naudotojų nėra.</p>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr><th>Vardas Pavardė</th><th>El. paštas</th><th>Rolė</th><th>Būsena</th><th>Veiksmai</th></tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id">
                  <td>{{ u.first_name }} {{ u.last_name }} ({{ u.username }})</td>
                  <td>{{ u.email || '—' }}</td>
                  <td>{{ roleLabel(u.role) }}</td>
                  <td>
                    <span :class="['badge', u.is_active ? 'used' : 'expired']">
                      {{ u.is_active ? 'Aktyvi' : 'Užblokuota' }}
                    </span>
                  </td>
                  <td>
                    <button v-if="u.is_active && u.id !== user?.id && u.role !== 'admin'" class="revoke-btn" @click="toggleUserStatus(u, false)">
                      Blokuoti
                    </button>
                    <button v-else-if="!u.is_active" class="copy-btn" style="padding:4px 11px;font-size:12px" @click="toggleUserStatus(u, true)">
                      Aktyvuoti
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <template v-else>
      <h2>Pakviesti vartotoją</h2>

      <div class="form-card">
        <form @submit.prevent="createInvite">
          <div class="invite-row">
            <div class="field">
              <label>El. paštas (informaciniam)</label>
              <input v-model="inviteEmail" type="email" placeholder="darbuotojas@imone.lt" required />
            </div>
            <div class="field field-role">
              <label>Vaidmuo</label>
              <select v-model="inviteRole">
                <option value="worker">Darbuotojas</option>
                <option value="manager">Vadybininkas</option>
                <option value="admin">Administratorius</option>
              </select>
            </div>
            <button type="submit" :disabled="inviteLoading">
              {{ inviteLoading ? 'Generuojama…' : 'Generuoti nuorodą' }}
            </button>
          </div>
          <p v-if="inviteError" class="error">{{ inviteError }}</p>
        </form>

        <div v-if="newLinkEmail" class="new-link-box">
          <p class="new-link-label">✓ Pakvietimas sukurtas ({{ newLinkEmail }})</p>
          <div class="link-row">
            <input class="link-input" :value="newLink" readonly @click="$event.target.select()" />
            <button type="button" class="copy-btn" @click="copyLink">
              {{ copied ? '✓ Nukopijuota' : 'Kopijuoti nuorodą' }}
            </button>
          </div>
          <p class="link-note">Galioja 7 dienas. Vienkartinis naudojimas (galite atidaryti šią nuorodą tiesiai naršyklėje net be SMTP).</p>
        </div>
      </div>

      <h2>Laukiantys pakvietimai</h2>
      <div v-if="invitesLoading" class="loading">Kraunama…</div>
      <div v-else>
        <p v-if="!invites.length" class="empty">Pakvietimų dar nėra.</p>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr><th>El. paštas</th><th>Vaidmuo</th><th>Būsena</th><th>Galioja iki</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="inv in invites" :key="inv.id">
                <td>{{ inv.email }}</td>
                <td>{{ roleLabel(inv.role) }}</td>
                <td>
                  <span :class="['badge', inv.used ? 'used' : isExpired(inv) ? 'expired' : 'pending']">
                    {{ inv.used ? 'Panaudota' : isExpired(inv) ? 'Pasibaigė' : 'Laukiama' }}
                  </span>
                </td>
                <td>{{ inv.expires_at.slice(0, 10) }}</td>
                <td style="display:flex;gap:6px">
                  <button v-if="!inv.used && !isExpired(inv)" class="copy-btn" style="padding:4px 10px;font-size:12px" @click="copyInviteRowLink(inv.token)">
                    Kopijuoti nuorodą
                  </button>
                  <button class="revoke-btn" @click="revokeInvite(inv.id)">Atšaukti</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import API from '../api'
import ProjectsPanel from '../components/ProjectsPanel.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import ThemeToggle from '../components/ThemeToggle.vue'

const confirmDialog = ref(null)

const { user, fetchMe, logout } = useAuth()

const activeTab = ref('invites')

const roleLabels = { worker: 'Darbuotojas', manager: 'Vadybininkas', admin: 'Administratorius' }
const roleLabel = (r) => roleLabels[r] ?? r

const invites = ref([])
const invitesLoading = ref(false)
const users = ref([])
const usersLoading = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('worker')
const inviteLoading = ref(false)
const inviteError = ref('')
const newLink = ref('')
const newLinkEmail = ref('')
const copied = ref(false)

function isExpired(inv) {
  return new Date(inv.expires_at) < new Date()
}

async function loadInvites() {
  invitesLoading.value = true
  const res = await API.get('/invites')
  invites.value = res.data
  invitesLoading.value = false
}

async function loadUsers() {
  usersLoading.value = true
  const res = await API.get('/users')
  users.value = res.data
  usersLoading.value = false
}

async function toggleUserStatus(u, activate) {
  if (!activate) {
    const ok = await confirmDialog.value.show(`Ar tikrai norite blokuoti naudotoją ${u.first_name} ${u.last_name}?`)
    if (!ok) return
    await API.patch(`/users/${u.id}/dismiss`)
  } else {
    await API.patch(`/users/${u.id}/reactivate`)
  }
  await loadUsers()
}

async function createInvite() {
  inviteError.value = ''
  inviteLoading.value = true
  newLink.value = ''
  copied.value = false
  try {
    const res = await API.post('/invites', { email: inviteEmail.value, role: inviteRole.value })
    newLink.value = `${window.location.origin}/register?token=${res.data.token}`
    newLinkEmail.value = inviteEmail.value
    inviteEmail.value = ''
    inviteRole.value = 'worker'
    await loadInvites()
  } catch (e) {
    inviteError.value = e.response?.data?.error || 'Nepavyko sukurti pakvietimo'
  } finally {
    inviteLoading.value = false
  }
}

async function revokeInvite(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite atšaukti šį pakvietimą?')
  if (!ok) return
  await API.delete(`/invites/${id}`)
  await loadInvites()
}

async function copyLink() {
  await navigator.clipboard.writeText(newLink.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function copyInviteRowLink(token) {
  const url = `${window.location.origin}/register?token=${token}`
  newLink.value = url
  await navigator.clipboard.writeText(url)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

onMounted(async () => {
  await fetchMe()
  await Promise.all([loadInvites(), loadUsers()])
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
  letter-spacing: -0.01em;
  display: none;
}

@media (min-width: 600px) {
  .app-name { display: inline; }
}

.tabs { display: flex; gap: 4px; flex: 1; }

.tab {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.tab:hover { background: var(--muted); color: var(--text-h); }
.tab.active { background: var(--accent-bg); color: var(--accent); }

.user-area { display: flex; align-items: center; gap: 12px; }
.username { font-size: 13px; color: var(--text); font-weight: 500; display: none; }

@media (min-width: 480px) {
  .username { display: inline; }
}

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

h2 { margin: 0 0 18px; }

.loading { color: var(--text); padding: 32px 0; text-align: center; font-size: 14px; }

/* ── Form card ── */
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(14px, 3vw, 22px) clamp(16px, 4vw, 24px);
  margin-bottom: 28px;
  box-shadow: var(--shadow-sm);
}

.invite-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 140px; }
.field-role { flex: 1; min-width: 130px; }

label { font-size: 13px; font-weight: 500; color: var(--text-h); }

input, select {
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

button[type="submit"] {
  padding: 9px 18px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  align-self: stretch;
  width: 100%;
  font-family: inherit;
  transition: background 0.15s;
}

button[type="submit"]:hover { background: var(--accent-hover); }
button:disabled { opacity: 0.55; cursor: default; }

@media (min-width: 640px) {
  button[type="submit"] { width: auto; align-self: flex-end; }
}

/* ── Invite link box ── */
.new-link-box {
  margin-top: 16px;
  padding: 14px 16px;
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-sm);
}

.new-link-label { font-size: 13px; color: var(--text-h); font-weight: 500; margin: 0 0 8px; }
.link-row { display: flex; align-items: center; gap: 10px; }

.link-text {
  flex: 1;
  font-size: 12px;
  word-break: break-all;
  white-space: normal;
  background: var(--surface);
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-h);
  display: block;
  border: 1px solid var(--accent-border);
}

.copy-btn {
  padding: 7px 14px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  font-family: inherit;
  transition: background 0.15s;
}

.copy-btn:hover { background: var(--accent-hover); }
.link-note { font-size: 12px; color: var(--text); margin: 8px 0 0; }

/* ── Table ── */
.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow-x: auto;
  box-shadow: var(--shadow-sm);
}

table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 460px; }

thead tr { background: var(--muted); border-bottom: 2px solid var(--border); }

th {
  text-align: left;
  padding: 10px 14px;
  color: var(--text);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  text-align: left;
  padding: 10px 14px;
  color: var(--text-h);
  border-bottom: 1px solid var(--border);
}

tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--muted); }

.empty { color: var(--text); font-size: 13px; padding: 14px 0; margin: 0; }

.revoke-btn {
  padding: 4px 11px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.revoke-btn:hover { border-color: var(--danger); color: var(--danger); }

.badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 99px;
}
.badge.pending  { background: var(--accent-bg); color: var(--accent); }
.badge.used     { background: #dcfce7; color: #166534; }
.badge.expired  { background: var(--danger-bg); color: #991b1b; }

.error { color: var(--danger); font-size: 13px; margin: 8px 0 0; }
</style>
