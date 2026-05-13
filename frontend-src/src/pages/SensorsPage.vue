<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Sensors</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadSensors" :loading="loading" class="q-mr-sm" />
      <q-btn color="secondary" label="Teach Sensor" icon="school" @click="startTeach" :loading="teaching" />
    </div>

    <!-- Teach Dialog -->
    <q-dialog v-model="teachDialogOpen" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center">
          <q-icon name="school" size="md" color="primary" class="q-mr-sm" />
          <span class="text-h6">Sensor Teach Mode</span>
        </q-card-section>
        <q-card-section>
          <div v-if="teaching" class="text-center">
            <q-spinner-dots size="40px" color="primary" />
            <div class="q-mt-sm">Waiting for sensor signal... Activate the sensor now.</div>
          </div>
          <div v-else-if="teachResult">
            <div v-if="teachResult.found" class="text-positive">
              <q-icon name="check_circle" /> Sensor learned!
              <div class="q-mt-sm">ID: {{ teachResult.foundId }}</div>
            </div>
            <div v-else class="text-negative">
              <q-icon name="cancel" /> No sensor found.
            </div>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-if="teaching" flat label="Stop Teaching" color="negative" @click="stopTeach" />
          <q-btn flat label="Close" color="primary" v-close-popup @click="closeTeachDialog" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Sensor Info Dialog -->
    <q-dialog v-model="infoDialogOpen">
      <q-card style="min-width: 500px">
        <q-card-section class="row items-center q-pb-none">
          <span class="text-h6">Sensor {{ selectedSensor?.id }} Info</span>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section v-if="selectedSensorInfo">
          <q-list dense>
            <q-item v-for="(value, key) in selectedSensorInfo" :key="key">
              <q-item-section>
                <q-item-label caption>{{ key }}</q-item-label>
                <q-item-label>{{ formatValue(value) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-section v-if="selectedSensorValues">
          <div class="text-subtitle2 q-mb-sm">Current Values</div>
          <q-list dense>
            <q-item v-for="(value, key) in selectedSensorValues" :key="key">
              <q-item-section>
                <q-item-label caption>{{ key }}</q-item-label>
                <q-item-label>{{ formatValue(value) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Sensors Table -->
    <q-table
      flat
      bordered
      :rows="sensors"
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
              {{ props.row.name || 'Sensor-' + props.row.id }}
              <q-icon name="edit" size="xs" class="q-ml-xs" />
            </span>
          </q-td>
          <q-td key="wind" :props="props">
            <q-badge color="info">{{ props.row.values?.wind_digital ?? '-' }}</q-badge>
          </q-td>
          <q-td key="rain" :props="props">
            <q-icon :name="props.row.values?.rain_digital ? 'water_drop' : 'wb_sunny'" :color="props.row.values?.rain_digital ? 'blue' : 'amber'" />
          </q-td>
          <q-td key="temp" :props="props">
            {{ props.row.values?.temp_digital ?? '-' }}°C
          </q-td>
          <q-td key="light" :props="props">
            {{ props.row.values?.light_digital ?? '-' }} lux
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs">
              <q-btn dense flat icon="sync" color="primary" @click="updateSensor(props.row.id)">
                <q-tooltip>Update Values</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="info" color="info" @click="showInfo(props.row)">
                <q-tooltip>Sensor Info</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="delete" color="negative" @click="confirmDelete(props.row)">
                <q-tooltip>Delete Sensor</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </q-tr>
      </template>

      <template v-slot:no-data>
        <div class="full-width row flex-center text-grey q-gutter-sm">
          <q-icon name="sensors_off" size="md" />
          <span>No sensors found. Use "Teach Sensor" to add one.</span>
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

const sensors = ref([])
const loading = ref(false)
const teaching = ref(false)
const teachDialogOpen = ref(false)
const teachResult = ref(null)
const infoDialogOpen = ref(false)
const selectedSensor = ref(null)
const selectedSensorInfo = ref(null)
const selectedSensorValues = ref(null)

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'left' },
  { name: 'wind', label: 'Wind', align: 'center' },
  { name: 'rain', label: 'Rain', align: 'center' },
  { name: 'temp', label: 'Temp', align: 'center' },
  { name: 'light', label: 'Light', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

function formatValue(val) {
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

async function loadSensors() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/sensors')
    sensors.value = Array.isArray(data) ? data : []
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load sensors', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function updateSensor(id) {
  try {
    await axios.post(`/api/sensors/${id}/update`)
    $q.notify({ color: 'positive', message: 'Sensor updated', icon: 'check' })
    await loadSensors()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to update sensor', icon: 'error' })
  }
}

function editLabel(sensor) {
  $q.dialog({
    title: 'Rename Sensor',
    message: 'Enter new label:',
    prompt: { model: sensor.name || `Sensor-${sensor.id}`, type: 'text' },
    cancel: true,
  }).onOk(async label => {
    try {
      await axios.put(`/api/sensors/${sensor.id}/setLabel`, { label })
      sensor.name = label
      $q.notify({ color: 'positive', message: 'Sensor renamed', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to rename', icon: 'error' })
    }
  })
}

function confirmDelete(sensor) {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete sensor ${sensor.name || sensor.id}?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await axios.delete(`/api/sensors/${sensor.id}`)
      $q.notify({ color: 'positive', message: 'Sensor deleted', icon: 'check' })
      await loadSensors()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to delete', icon: 'error' })
    }
  })
}

async function showInfo(sensor) {
  selectedSensor.value = sensor
  try {
    const [infoRes, valsRes] = await Promise.all([
      axios.get(`/api/sensors/${sensor.id}/info`),
      axios.get(`/api/sensors/${sensor.id}/values`),
    ])
    selectedSensorInfo.value = infoRes.data
    selectedSensorValues.value = valsRes.data
    infoDialogOpen.value = true
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load sensor info', icon: 'error' })
  }
}

// Teach flow
let teachPollInterval = null

async function startTeach() {
  teachDialogOpen.value = true
  teaching.value = true
  teachResult.value = null
  try {
    await axios.post('/api/sensors/teach/start')
    teachPollInterval = setInterval(pollTeachResult, 2000)
  } catch (e) {
    teaching.value = false
    $q.notify({ color: 'negative', message: 'Failed to start teaching', icon: 'error' })
  }
}

async function pollTeachResult() {
  try {
    const { data } = await axios.get('/api/sensors/teach/result')
    if (data && (data.found || data.finished)) {
      clearInterval(teachPollInterval)
      teaching.value = false
      teachResult.value = data
      if (data.found) await loadSensors()
    }
  } catch (e) {
    // continue polling
  }
}

async function stopTeach() {
  clearInterval(teachPollInterval)
  try {
    await axios.post('/api/sensors/teach/stop')
  } catch (e) {
    // ignore
  }
  teaching.value = false
}

function closeTeachDialog() {
  if (teaching.value) stopTeach()
  teachResult.value = null
}

onMounted(loadSensors)
</script>

<style scoped>
</style>
