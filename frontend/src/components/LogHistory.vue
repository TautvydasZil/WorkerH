<template>
  <ConfirmDialog ref="confirmDialog" />
  <div class="history">
    <div class="history-header">
      <h3>{{ title }}</h3>
      <span v-if="entries.length" class="count">{{ entries.length }} {{ entryWord }}</span>
    </div>

    <p v-if="!entries.length" class="empty">Įrašų dar nėra.</p>

    <ul v-else>
      <li v-for="entry in entries" :key="entry.id" class="entry">
        <div class="entry-main">
          <span class="entry-date">{{ entry.date }}</span>
          <template v-if="type === 'hours'">
            <span v-if="entry.start_time && entry.end_time" class="entry-time">
              {{ entry.start_time }}–{{ entry.end_time }}
              <span v-if="entry.lunch_break">(-{{ entry.lunch_break }}min.)</span>
            </span>
            <span class="entry-hours">{{ entry.hours }}val.</span>
          </template>
          <span v-if="entry.project_name" class="entry-project">{{ entry.project_name }}</span>
          <span v-if="entry.task_title" class="entry-project">📋 {{ entry.task_title }}</span>
          <span v-if="entry.notes" class="entry-notes">{{ entry.notes }}</span>
        </div>
        <div class="entry-actions">
          <button v-if="type === 'hours'" class="edit-btn" title="Redaguoti" @click="emit('edit', entry)">✎</button>
          <button class="delete-btn" title="Ištrinti" @click="remove(entry.id)">✕</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import API from '../api'
import ConfirmDialog from './ConfirmDialog.vue'

const confirmDialog = ref(null)

const props = defineProps({
  title: String,
  entries: Array,
  type: String
})

const emit = defineEmits(['deleted', 'edit'])

const entryWord = computed(() => {
  const n = props.entries.length
  if (n % 10 === 1 && n % 100 !== 11) return 'įrašas'
  if (n % 10 >= 2 && n % 10 <= 9 && !(n % 100 >= 12 && n % 100 <= 19)) return 'įrašai'
  return 'įrašų'
})

async function remove(id) {
  const ok = await confirmDialog.value.show('Ar tikrai norite ištrinti šį įrašą?')
  if (!ok) return
  await API.delete(`/${props.type}/${id}`)
  emit('deleted')
}
</script>

<style scoped>
.history {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

h3 { margin: 0; font-size: 15px; }

.count {
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  background: var(--muted);
  padding: 2px 8px;
  border-radius: 99px;
  border: 1px solid var(--border);
}

.empty { color: var(--text); font-size: 13px; margin: 0; }

ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 5px; }

.entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  transition: background 0.12s;
}

.entry:hover { background: var(--muted); }

.entry-main { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; flex-wrap: wrap; }

.entry-date { font-size: 13px; color: var(--text-h); font-weight: 600; white-space: nowrap; }

.entry-time { font-size: 12px; color: var(--text); white-space: nowrap; }

.entry-hours {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 2px 9px;
  border-radius: 99px;
  white-space: nowrap;
  border: 1px solid var(--accent-border);
}

.entry-project {
  font-size: 11px;
  font-weight: 500;
  color: var(--text);
  background: var(--muted);
  padding: 2px 8px;
  border-radius: 99px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
  border: 1px solid var(--border);
}

.entry-notes {
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-style: italic;
}

.entry-actions { display: flex; align-items: center; gap: 2px; flex-shrink: 0; margin-left: 8px; }

.edit-btn, .delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 7px;
  border-radius: var(--radius-sm);
  opacity: 0.4;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
  color: var(--text);
  font-family: inherit;
}

.edit-btn:hover { opacity: 1; color: var(--accent); background: var(--accent-bg); }
.delete-btn:hover { opacity: 1; color: var(--danger); background: var(--danger-bg); }
</style>
