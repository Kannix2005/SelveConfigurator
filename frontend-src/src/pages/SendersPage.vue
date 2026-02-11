<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Senders (Remote Controls)</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadSenders" :loading="loading" class="q-mr-sm" />
      <q-btn color="secondary" label="Teach Sender" icon="school" @click="startTeach" :loading="teaching" />
    </div>

    <!-- Teach Dialog -->
    <q-dialog v-model="teachDialogOpen" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center">
          <q-icon name="school" size="md" color="primary" class="q-mr-sm" />
          <span class="text-h6">Sender Teach Mode</span>
        </q-card-section>
        <q-card-section>
          <div v-if="teaching" class="text-center">
            <q-spinner-dots size="40px" color="primary" />
            <div class="q-mt-sm">Waiting for sender signal... Press a button on the remote control.</div>
          </div>
          <div v-else-if="teachResult">
            <div v-if="teachResult.found" class="text-positive">
              <q-icon name="check_circle" /> Sender learned!
              <div class="q-mt-sm">Address: {{ teachResult.address }}</div>
            </div>
            <div v-else class="text-negative">
              <q-icon name="cancel" /> No sender found.
            </div>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-if="teaching" flat label="Stop Teaching" color="negative" @click="stopTeach" />
          <q-btn flat label="Close" color="primary" v-close-popup @click="closeTeachDialog" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Sender Info Dialog -->
    <q-dialog v-model="infoDialogOpen">
      <q-card style="min-width: 500px">
        <q-card-section class="row items-center q-pb-none">
          <span class="text-h6">Sender {{ selectedSender?.id }} Info</span>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section v-if="selectedSenderInfo">
          <q-list dense>
            <q-item v-for="(value, key) in selectedSenderInfo" :key="key">
              <q-item-section>
                <q-item-label caption>{{ key }}</q-item-label>
                <q-item-label>{{ formatValue(value) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-section v-if="selectedSenderValues">
          <div class="text-subtitle2 q-mb-sm">Current Values</div>
          <q-list dense>
            <q-item v-for="(value, key) in selectedSenderValues" :key="key">
              <q-item-section>
                <q-item-label caption>{{ key }}</q-item-label>
                <q-item-label>{{ formatValue(value) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Senders Table -->
    <q-table
      flat
      bordered
      :rows="senders"
      :columns="columns"
      row-key="id"
      :loading="loading"
      :pagination="{ rowsPerPage: 20 }"
    >
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">{{ props.row.id }}</q-td>
          <q-td key="name" :props="props">
            <span class="cursor-pointer text-primary" @click="editLabel(props.row)">
              {{ props.row.name || 'Sender-' + props.row.id }}
              <q-icon name="edit" size="xs" class="q-ml-xs" />
            </span>
          </q-td>
          <q-td key="channel" :props="props">
            {{ props.row.info?.rf_channel ?? '-' }}
          </q-td>
          <q-td key="address" :props="props">
            {{ props.row.info?.rf_address ?? '-' }}
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs">
              <q-btn dense flat icon="sync" color="primary" @click="updateSender(props.row.id)">
                <q-tooltip>Update Values</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="info" color="info" @click="showInfo(props.row)">
                <q-tooltip>Sender Info</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="delete" color="negative" @click="confirmDelete(props.row)">
                <q-tooltip>Delete Sender</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </q-tr>
      </template>

      <template v-slot:no-data>
        <div class="full-width row flex-center text-grey q-gutter-sm">
          <q-icon name="settings_remote" size="md" />
          <span>No senders found. Use "Teach Sender" to add one.</span>
        </div>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

const $q = useQuasar()

const senders = ref([])
const loading = ref(false)
const teaching = ref(false)
const teachDialogOpen = ref(false)
const teachResult = ref(null)
const infoDialogOpen = ref(false)
const selectedSender = ref(null)
const selectedSenderInfo = ref(null)
const selectedSenderValues = ref(null)

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'left' },
  { name: 'channel', label: 'Channel', align: 'center' },
  { name: 'address', label: 'Address', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

function formatValue(val) {
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

async function loadSenders() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/senders')
    senders.value = Array.isArray(data) ? data : []
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load senders', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function updateSender(id) {
  try {
    await axios.post(`/api/senders/${id}/update`)
    $q.notify({ color: 'positive', message: 'Sender updated', icon: 'check' })
    await loadSenders()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to update sender', icon: 'error' })
  }
}

function editLabel(sender) {
  $q.dialog({
    title: 'Rename Sender',
    message: 'Enter new label:',
    prompt: { model: sender.name || `Sender-${sender.id}`, type: 'text' },
    cancel: true,
  }).onOk(async label => {
    try {
      await axios.put(`/api/senders/${sender.id}/setLabel`, { label })
      sender.name = label
      $q.notify({ color: 'positive', message: 'Sender renamed', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to rename', icon: 'error' })
    }
  })
}

function confirmDelete(sender) {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete sender ${sender.name || sender.id}?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await axios.delete(`/api/senders/${sender.id}`)
      $q.notify({ color: 'positive', message: 'Sender deleted', icon: 'check' })
      await loadSenders()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to delete', icon: 'error' })
    }
  })
}

async function showInfo(sender) {
  selectedSender.value = sender
  try {
    const [infoRes, valsRes] = await Promise.all([
      axios.get(`/api/senders/${sender.id}/info`),
      axios.get(`/api/senders/${sender.id}/values`),
    ])
    selectedSenderInfo.value = infoRes.data
    selectedSenderValues.value = valsRes.data
    infoDialogOpen.value = true
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load sender info', icon: 'error' })
  }
}

// Teach flow
let teachPollInterval = null

async function startTeach() {
  teachDialogOpen.value = true
  teaching.value = true
  teachResult.value = null
  try {
    await axios.post('/api/senders/teach/start')
    teachPollInterval = setInterval(pollTeachResult, 2000)
  } catch (e) {
    teaching.value = false
    $q.notify({ color: 'negative', message: 'Failed to start teaching', icon: 'error' })
  }
}

async function pollTeachResult() {
  try {
    const { data } = await axios.get('/api/senders/teach/result')
    if (data && (data.found || data.finished)) {
      clearInterval(teachPollInterval)
      teaching.value = false
      teachResult.value = data
      if (data.found) await loadSenders()
    }
  } catch (e) {
    // continue polling
  }
}

async function stopTeach() {
  clearInterval(teachPollInterval)
  try {
    await axios.post('/api/senders/teach/stop')
  } catch (e) {
    // ignore
  }
  teaching.value = false
}

function closeTeachDialog() {
  if (teaching.value) stopTeach()
  teachResult.value = null
}

onMounted(loadSenders)
</script>

<style scoped>
</style>
