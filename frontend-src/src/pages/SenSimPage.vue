<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Sensor Simulation</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadSenSims" :loading="loading" class="q-mr-sm" />
      <q-btn color="secondary" label="Add SenSim" icon="add" @click="openAddDialog" />
    </div>

    <!-- Add SenSim Dialog -->
    <q-dialog v-model="addDialogOpen" persistent>
      <q-card style="min-width: 380px">
        <q-card-section class="row items-center q-pb-none">
          <span class="text-h6">Add Sensor Simulation</span>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model.number="addForm.id" label="SenSim Slot ID (0–4)" type="number" :min="0" :max="4" outlined
            hint="Gateway supports up to 5 sensor simulation slots (0–4)" />
          <q-input v-model.number="addForm.actor_id" label="Actor Device ID" type="number" :min="0" outlined
            hint="ID of the Commeo device this SenSim will be linked to" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey" v-close-popup />
          <q-btn flat label="Add" color="positive" @click="addSenSim" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Info Banner -->
    <q-banner class="bg-blue-1 q-mb-md" rounded>
      <template v-slot:avatar>
        <q-icon name="info" color="primary" />
      </template>
      Sensor simulations allow you to create virtual sensors that broadcast simulated wind, rain, 
      temperature, and light values. Use them to test automations without real sensor hardware.
    </q-banner>

    <!-- Edit Values Dialog -->
    <q-dialog v-model="editDialogOpen" persistent>
      <q-card style="min-width: 500px">
        <q-card-section class="row items-center q-pb-none">
          <span class="text-h6">Edit SenSim #{{ editingSenSim?.id }} Values</span>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">Digital Values (Alarm Thresholds)</div>
          <div class="row q-gutter-md q-mb-md">
            <q-toggle v-model="editValues.wind_digital" label="Wind Alarm" color="orange" />
            <q-toggle v-model="editValues.rain_digital" label="Rain Alarm" color="blue" />
            <q-toggle v-model="editValues.temp_digital" label="Frost Alarm" color="cyan" />
            <q-toggle v-model="editValues.light_digital" label="Light Threshold" color="amber" />
          </div>
          <div class="text-subtitle2 q-mb-sm">Analog Values</div>
          <div class="q-gutter-md">
            <div>
              <div class="text-caption">Wind Speed: {{ editValues.wind_analog }}%</div>
              <q-slider v-model="editValues.wind_analog" :min="0" :max="100" label color="orange" />
            </div>
            <div>
              <div class="text-caption">Sun 1 Level: {{ editValues.sun_1_analog }}%</div>
              <q-slider v-model="editValues.sun_1_analog" :min="0" :max="100" label color="yellow" />
            </div>
            <div>
              <div class="text-caption">Temperature: {{ (editValues.temp_analog / 10).toFixed(1) }}°C</div>
              <q-slider v-model="editValues.temp_analog" :min="-400" :max="800" :step="1" label 
                :label-value="(editValues.temp_analog / 10).toFixed(1) + '°C'" color="red" />
            </div>
            <div>
              <div class="text-caption">Daylight Level: {{ editValues.day_light_analog }}%</div>
              <q-slider v-model="editValues.day_light_analog" :min="0" :max="100" label color="amber" />
            </div>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey" v-close-popup />
          <q-btn flat label="Apply & Drive" color="primary" @click="applyAndDrive" />
          <q-btn flat label="Save Values" color="positive" @click="saveValues" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- SenSim Table -->
    <q-table
      flat
      bordered
      :rows="senSims"
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
              {{ props.row.name || 'SenSim-' + props.row.id }}
              <q-icon name="edit" size="xs" class="q-ml-xs" />
            </span>
          </q-td>
          <q-td key="activity" :props="props">
            <q-toggle
              :model-value="props.row.activity === 1"
              @update:model-value="toggleActivity(props.row, $event)"
              color="positive"
              :label="props.row.activity === 1 ? 'ON' : 'OFF'"
            />
          </q-td>
          <q-td key="wind" :props="props">
            <q-badge :color="props.row.values?.wind_digital ? 'orange' : 'grey'">
              {{ props.row.values?.wind_analog ?? 0 }}%
            </q-badge>
          </q-td>
          <q-td key="rain" :props="props">
            <q-icon
              :name="props.row.values?.rain_digital ? 'water_drop' : 'wb_sunny'"
              :color="props.row.values?.rain_digital ? 'blue' : 'amber'"
            />
            <span class="q-ml-xs">{{ props.row.values?.rain_digital ? 'Rain' : 'Dry' }}</span>
          </q-td>
          <q-td key="temp" :props="props">
            <q-badge :color="props.row.values?.temp_digital ? 'cyan' : 'grey'">
              {{ ((props.row.values?.temp_analog ?? 0) / 10).toFixed(1) }}°C
            </q-badge>
          </q-td>
          <q-td key="light" :props="props">
            <q-badge :color="props.row.values?.light_digital ? 'amber' : 'grey'">
              {{ props.row.values?.day_light_analog ?? 0 }}%
            </q-badge>
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs">
              <q-btn dense flat icon="tune" color="primary" @click="openEditDialog(props.row)">
                <q-tooltip>Edit Values</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="send" color="positive" @click="driveSenSim(props.row.id)">
                <q-tooltip>Send/Drive Values</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="save" color="info" @click="storeSenSim(props.row.id)">
                <q-tooltip>Store to Memory</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="delete" color="negative" @click="confirmDelete(props.row)">
                <q-tooltip>Delete</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </q-tr>
      </template>

      <template v-slot:no-data>
        <div class="full-width row flex-center text-grey q-gutter-sm">
          <q-icon name="science" size="md" />
          <span>No sensor simulations found. They must be configured via the gateway first.</span>
        </div>
      </template>
    </q-table>

    <!-- Factory Reset -->
    <q-card flat bordered class="q-mt-md bg-red-1">
      <q-card-section>
        <div class="row items-center">
          <div>
            <div class="text-subtitle1 text-negative">Factory Reset All Sensor Simulations</div>
            <div class="text-caption">This will delete all sensor simulation configurations.</div>
          </div>
          <q-space />
          <q-btn color="negative" label="Factory Reset" icon="warning" @click="confirmFactoryReset" />
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

const $q = useQuasar()

const senSims = ref([])
const loading = ref(false)
const editDialogOpen = ref(false)
const addDialogOpen = ref(false)
const addForm = ref({ id: 0, actor_id: 0 })
const editingSenSim = ref(null)
const editValues = ref({
  wind_digital: false,
  rain_digital: false,
  temp_digital: false,
  light_digital: false,
  wind_analog: 0,
  sun_1_analog: 0,
  temp_analog: 200, // 20.0°C
  day_light_analog: 0,
})

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'left' },
  { name: 'activity', label: 'Active', align: 'center' },
  { name: 'wind', label: 'Wind', align: 'center' },
  { name: 'rain', label: 'Rain', align: 'center' },
  { name: 'temp', label: 'Temp', align: 'center' },
  { name: 'light', label: 'Light', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

async function loadSenSims() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/sensim')
    senSims.value = Array.isArray(data) ? data : []
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load sensor simulations', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function toggleActivity(row, active) {
  try {
    await axios.post(`/api/sensim/${row.id}/setConfig`, { activity: active ? 1 : 0 })
    row.activity = active ? 1 : 0
    $q.notify({ color: 'positive', message: `SenSim ${active ? 'activated' : 'deactivated'}`, icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to update config', icon: 'error' })
  }
}

function editLabel(row) {
  $q.dialog({
    title: 'Rename Sensor Simulation',
    message: 'Enter new label:',
    prompt: { model: row.name || `SenSim-${row.id}`, type: 'text' },
    cancel: true,
  }).onOk(async label => {
    try {
      await axios.put(`/api/sensim/${row.id}/setLabel`, { label })
      row.name = label
      $q.notify({ color: 'positive', message: 'Renamed', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to rename', icon: 'error' })
    }
  })
}

function openEditDialog(row) {
  editingSenSim.value = row
  editValues.value = {
    wind_digital: row.values?.wind_digital ?? false,
    rain_digital: row.values?.rain_digital ?? false,
    temp_digital: row.values?.temp_digital ?? false,
    light_digital: row.values?.light_digital ?? false,
    wind_analog: row.values?.wind_analog ?? 0,
    sun_1_analog: row.values?.sun_1_analog ?? 0,
    temp_analog: row.values?.temp_analog ?? 200,
    day_light_analog: row.values?.day_light_analog ?? 0,
  }
  editDialogOpen.value = true
}

async function saveValues() {
  if (!editingSenSim.value) return
  try {
    await axios.post(`/api/sensim/${editingSenSim.value.id}/setValues`, editValues.value)
    $q.notify({ color: 'positive', message: 'Values saved', icon: 'check' })
    editDialogOpen.value = false
    await loadSenSims()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to save values', icon: 'error' })
  }
}

async function applyAndDrive() {
  if (!editingSenSim.value) return
  try {
    await axios.post(`/api/sensim/${editingSenSim.value.id}/setValues`, editValues.value)
    await axios.post(`/api/sensim/${editingSenSim.value.id}/drive`)
    $q.notify({ color: 'positive', message: 'Values applied and driven', icon: 'check' })
    editDialogOpen.value = false
    await loadSenSims()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to apply values', icon: 'error' })
  }
}

async function driveSenSim(id) {
  try {
    await axios.post(`/api/sensim/${id}/drive`)
    $q.notify({ color: 'positive', message: 'Sensor simulation driven', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to drive', icon: 'error' })
  }
}

async function storeSenSim(id) {
  try {
    await axios.post(`/api/sensim/${id}/store`)
    $q.notify({ color: 'positive', message: 'Values stored to memory', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to store', icon: 'error' })
  }
}

function confirmDelete(row) {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete sensor simulation "${row.name || row.id}"?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await axios.delete(`/api/sensim/${row.id}`)
      $q.notify({ color: 'positive', message: 'Deleted', icon: 'check' })
      await loadSenSims()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to delete', icon: 'error' })
    }
  })
}

function confirmFactoryReset() {
  $q.dialog({
    title: 'Factory Reset Sensor Simulations',
    message: 'This will delete ALL sensor simulation configurations. Are you sure?',
    cancel: true,
    persistent: true,
    ok: { label: 'Reset', color: 'negative' },
  }).onOk(async () => {
    try {
      await axios.post('/api/sensim/factoryReset')
      $q.notify({ color: 'positive', message: 'Factory reset complete', icon: 'check' })
      await loadSenSims()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Factory reset failed', icon: 'error' })
    }
  })
}

function openAddDialog() {
  addForm.value = { id: 0, actor_id: 0 }
  addDialogOpen.value = true
}

async function addSenSim() {
  try {
    await axios.post(`/api/sensim/${addForm.value.id}/store`, { actor_id: addForm.value.actor_id })
    $q.notify({ color: 'positive', message: `SenSim slot ${addForm.value.id} added`, icon: 'check' })
    addDialogOpen.value = false
    await loadSenSims()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to add SenSim', icon: 'error' })
  }
}

onMounted(loadSenSims)
</script>

<style scoped>
</style>
