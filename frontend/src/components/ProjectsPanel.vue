<template>
  <ConfirmDialog ref="confirmDialog" />
  <div class="projects-panel">
    <div class="panel-header">
      <h2>Projektai ir užduotys</h2>
      <button v-if="!showForm" class="add-btn" @click="startCreate">+ Pridėti projektą</button>
    </div>

    <!-- Create / Edit Project form -->
    <div v-if="showForm" class="form-card">
      <h3>{{ editId ? 'Redaguoti projektą' : 'Naujas projektas' }}</h3>
      <form @submit.prevent="save">
        <div class="field">
          <label>Pavadinimas</label>
          <input v-model="form.name" type="text" required placeholder="Projekto pavadinimas" />
        </div>
        <div class="field">
          <label>Vieta žemėlapyje</label>
          <MapPicker v-model="form.location" />
        </div>
        <p v-if="formError" class="error">{{ formError }}</p>
        <div class="form-actions">
          <button type="submit" :disabled="saving">{{ saving ? 'Saugoma…' : (editId ? 'Išsaugoti' : 'Sukurti') }}</button>
          <button type="button" class="cancel-btn" @click="cancelForm">Atšaukti</button>
        </div>
      </form>
    </div>

    <!-- Project list -->
    <div v-if="loadingProjects" class="loading">Kraunama…</div>
    <div v-else>
      <p v-if="!projects.length && !showForm" class="empty">Projektų dar nėra.</p>

      <!-- Active projects -->
      <template v-if="activeProjects.length">
        <p class="section-label">Aktyvūs ({{ activeProjects.length }})</p>
        <ul class="project-list">
          <li v-for="p in activeProjects" :key="p.id" class="project-card-wrap">
            <div class="project-card">
              <div class="project-info">
                <span class="project-name">{{ p.name }}</span>
                <span v-if="p.address" class="project-address">📍 {{ p.address }}</span>
                <span v-else-if="p.latitude != null" class="project-address">
                  📍 {{ p.latitude.toFixed(5) }}, {{ p.longitude.toFixed(5) }}
                </span>
              </div>
              <div class="project-actions">
                <button class="tasks-btn" @click="toggleTasks(p.id)">
                  📋 Užduotys ({{ (tasksByProject[p.id] || []).length }})
                </button>
                <button class="complete-btn" @click="toggleComplete(p)">✓ Užbaigti</button>
                <button class="edit-btn" @click="startEdit(p)">Redaguoti</button>
                <button class="delete-btn" @click="remove(p.id)">Ištrinti</button>
              </div>
            </div>

            <!-- Tasks section for project -->
            <div v-if="expandedProjectId === p.id" class="tasks-section">
              <div class="tasks-header">
                <h4>Projekto užduotys</h4>
                <button v-if="taskFormProjectId !== p.id" class="add-task-btn" @click="startCreateTask(p.id)">
                  + Nauja užduotis
                </button>
              </div>

              <!-- Task Create / Edit Form -->
              <form v-if="taskFormProjectId === p.id" class="task-form" @submit.prevent="saveTask(p.id)">
                <div class="task-form-row">
                  <input v-model="taskForm.title" type="text" required placeholder="Užduoties pavadinimas" />
                  <select v-model="taskForm.status">
                    <option value="todo">Suplanuota</option>
                    <option value="in_progress">Vykdoma</option>
                    <option value="done">Atlikta</option>
                  </select>
                </div>
                <input v-model="taskForm.description" type="text" placeholder="Aprašymas (neprivaloma)" />
                <p v-if="taskError" class="error">{{ taskError }}</p>
                <div class="form-actions">
                  <button type="submit" :disabled="taskSaving">
                    {{ taskSaving ? 'Saugoma…' : (editTaskId ? 'Išsaugoti' : 'Pridėti užduotį') }}
                  </button>
                  <button type="button" class="cancel-btn" @click="cancelTaskForm">Atšaukti</button>
                </div>
              </form>

              <p v-if="!(tasksByProject[p.id] || []).length && taskFormProjectId !== p.id" class="empty">
                Šiam projektui dar nepriskirta užduočių.
              </p>
              <ul v-else class="task-list">
                <li v-for="t in (tasksByProject[p.id] || [])" :key="t.id" class="task-item">
                  <div class="task-info">
                    <div class="task-title-row">
                      <span class="task-title">{{ t.title }}</span>
                      <span :class="['task-badge', t.status]">{{ statusLabel(t.status) }}</span>
                    </div>
                    <span v-if="t.description" class="task-desc">{{ t.description }}</span>
                  </div>
                  <div class="task-actions">
                    <button class="edit-btn" @click="startEditTask(p.id, t)">Redaguoti</button>
                    <button class="delete-btn" @click="removeTask(p.id, t.id)">Šalinti</button>
                  </div>
                </li>
              </ul>
            </div>
          </li>
        </ul>
      </template>

      <!-- Completed projects -->
      <template v-if="completedProjects.length">
        <button class="toggle-completed-btn" @click="showCompleted = !showCompleted">
          {{ showCompleted ? '▲' : '▼' }} Užbaigti ({{ completedProjects.length }})
        </button>
        <ul v-if="showCompleted" class="project-list completed-list">
          <li v-for="p in completedProjects" :key="p.id" class="project-card-wrap">
            <div class="project-card completed">
              <div class="project-info">
                <span class="project-name">{{ p.name }}</span>
                <span v-if="p.address" class="project-address">📍 {{ p.address }}</span>
                <span v-else-if="p.latitude != null" class="project-address">
                  📍 {{ p.latitude.toFixed(5) }}, {{ p.longitude.toFixed(5) }}
                </span>
              </div>
              <div class="project-actions">
                <button class="reopen-btn" @click="toggleComplete(p)">↩ Atnaujinti</button>
                <button class="delete-btn" @click="remove(p.id)">Ištrinti</button>
              </div>
            </div>
          </li>
        </ul>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapPicker from './MapPicker.vue'
import API from '../api'
import ConfirmDialog from './ConfirmDialog.vue'

const confirmDialog = ref(null)

const projects = ref([])
const tasksByProject = ref({})
const expandedProjectId = ref(null)
const loadingProjects = ref(true)
const showForm = ref(false)
const showCompleted = ref(false)
const editId = ref(null)
const saving = ref(false)
const formError = ref('')

// Task form state
const taskFormProjectId = ref(null)
const editTaskId = ref(null)
const taskSaving = ref(false)
const taskError = ref('')
const taskForm = ref({ title: '', description: '', status: 'todo' })

const activeProjects    = computed(() => projects.value.filter(p => !p.is_completed))
const completedProjects = computed(() => projects.value.filter(p => p.is_completed))

const emptyForm = () => ({ name: '', location: null })
const form = ref(emptyForm())

function statusLabel(s) {
  return { todo: 'Suplanuota', in_progress: 'Vykdoma', done: 'Atlikta' }[s] || s
}

async function loadProjects() {
  loadingProjects.value = true
  const res = await API.get('/projects')
  projects.value = res.data
  await Promise.all(res.data.map(p => loadTasksForProject(p.id)))
  loadingProjects.value = false
}

async function loadTasksForProject(projectId) {
  try {
    const res = await API.get(`/projects/${projectId}/tasks`)
    tasksByProject.value = { ...tasksByProject.value, [projectId]: res.data }
  } catch {
    tasksByProject.value = { ...tasksByProject.value, [projectId]: [] }
  }
}

function toggleTasks(projectId) {
  if (expandedProjectId.value === projectId) {
    expandedProjectId.value = null
    cancelTaskForm()
  } else {
    expandedProjectId.value = projectId
    cancelTaskForm()
    loadTasksForProject(projectId)
  }
}

function startCreateTask(projectId) {
  taskFormProjectId.value = projectId
  editTaskId.value = null
  taskForm.value = { title: '', description: '', status: 'todo' }
  taskError.value = ''
}

function startEditTask(projectId, task) {
  taskFormProjectId.value = projectId
  editTaskId.value = task.id
  taskForm.value = {
    title: task.title,
    description: task.description || '',
    status: task.status || 'todo'
  }
  taskError.value = ''
}

function cancelTaskForm() {
  taskFormProjectId.value = null
  editTaskId.value = null
  taskError.value = ''
}

async function saveTask(projectId) {
  taskError.value = ''
  taskSaving.value = true
  try {
    const payload = {
      title: taskForm.value.title,
      description: taskForm.value.description,
      status: taskForm.value.status
    }
    if (editTaskId.value) {
      await API.put(`/projects/${projectId}/tasks/${editTaskId.value}`, payload)
    } else {
      await API.post(`/projects/${projectId}/tasks`, payload)
    }
    cancelTaskForm()
    await loadTasksForProject(projectId)
  } catch (e) {
    taskError.value = e.response?.data?.error || 'Nepavyko išsaugoti užduoties'
  } finally {
    taskSaving.value = false
  }
}

async function removeTask(projectId, taskId) {
  const ok = await confirmDialog.value.show('Ar tikrai norite pašalinti šią užduotį?')
  if (!ok) return
  await API.delete(`/projects/${projectId}/tasks/${taskId}`)
  await loadTasksForProject(projectId)
}

function startCreate() {
  editId.value = null
  form.value = emptyForm()
  formError.value = ''
  showForm.value = true
}

function startEdit(p) {
  editId.value = p.id
  form.value = {
    name: p.name,
    location: p.latitude != null
      ? { lat: p.latitude, lng: p.longitude, address: p.address }
      : null
  }
  formError.value = ''
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  editId.value = null
  form.value = emptyForm()
}

async function save() {
  formError.value = ''
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      latitude: form.value.location?.lat ?? null,
      longitude: form.value.location?.lng ?? null,
      address: form.value.location?.address ?? null
    }
    if (editId.value) {
      await API.put(`/projects/${editId.value}`, payload)
    } else {
      await API.post('/projects', payload)
    }
    cancelForm()
    await loadProjects()
  } catch (e) {
    formError.value = e.response?.data?.error || 'Nepavyko išsaugoti'
  } finally {
    saving.value = false
  }
}

async function toggleComplete(p) {
  await API.patch(`/projects/${p.id}/complete`)
  await loadProjects()
}

async function remove(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite ištrinti šį projektą?')
  if (!ok) return
  await API.delete(`/projects/${id}`)
  await loadProjects()
}

onMounted(loadProjects)
</script>

<style scoped>
.projects-panel { display: flex; flex-direction: column; gap: 18px; }

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header h2 { margin: 0; }

.add-btn, .add-task-btn {
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
  transition: background 0.15s;
}

.add-task-btn { padding: 6px 12px; font-size: 12px; }
.add-btn:hover, .add-task-btn:hover { background: var(--accent-hover); }

.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  box-shadow: var(--shadow-sm);
}

h3 { margin: 0 0 16px; font-size: 15px; }
h4 { margin: 0; font-size: 13px; color: var(--text-h); }

form { display: flex; flex-direction: column; gap: 14px; }

.field { display: flex; flex-direction: column; gap: 6px; }

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

.form-actions { display: flex; gap: 10px; }

button[type="submit"] {
  padding: 10px 20px;
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

.cancel-btn {
  padding: 10px 16px;
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

.loading { color: var(--text); padding: 32px 0; text-align: center; font-size: 14px; }

.empty { color: var(--text); font-size: 13px; margin: 0; }

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text);
  margin: 0 0 8px;
}

.toggle-completed-btn {
  margin: 16px 0 8px;
  padding: 0;
  background: none;
  border: none;
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.toggle-completed-btn:hover { color: var(--text-h); }

.project-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.completed-list { margin-top: 4px; }

.project-card-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: border-color 0.15s;
}

.project-card-wrap:hover { border-color: var(--accent-border); }

.project-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  flex-wrap: wrap;
}

.project-card.completed { opacity: 0.6; }
.project-card.completed .project-name { text-decoration: line-through; color: var(--text); }

.project-info { display: flex; flex-direction: column; gap: 3px; flex: 1; }
.project-name { font-size: 14px; font-weight: 600; color: var(--text-h); }
.project-address { font-size: 12px; color: var(--text); }
.project-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.tasks-btn, .edit-btn, .reopen-btn, .delete-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.tasks-btn { border-color: var(--accent-border); color: var(--accent); background: var(--accent-bg); }
.tasks-btn:hover { background: var(--accent); color: #fff; }
.edit-btn:hover, .reopen-btn:hover { border-color: var(--accent); color: var(--accent); }
.delete-btn:hover { border-color: var(--danger); color: var(--danger); }

.complete-btn {
  padding: 5px 13px;
  background: transparent;
  border: 1.5px solid #16a34a;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: #16a34a;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.complete-btn:hover { background: #16a34a; color: #fff; }

/* Tasks subsection */
.tasks-section {
  border-top: 1px solid var(--border);
  background: var(--muted);
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-form-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.task-form-row input { flex: 2; min-width: 180px; }
.task-form-row select { flex: 1; min-width: 130px; }

.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  flex-wrap: wrap;
}

.task-info { display: flex; flex-direction: column; gap: 3px; flex: 1; }
.task-title-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.task-title { font-size: 13px; font-weight: 600; color: var(--text-h); }
.task-desc { font-size: 12px; color: var(--text); }
.task-actions { display: flex; gap: 6px; }

.task-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
}
.task-badge.todo { background: var(--muted); color: var(--text); border: 1px solid var(--border); }
.task-badge.in_progress { background: var(--accent-bg); color: var(--accent); }
.task-badge.done { background: #dcfce7; color: #166534; }

.error { color: var(--danger); font-size: 13px; margin: 0; }
</style>
