<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Devices</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadDevices" :loading="loading" class="q-mr-sm" />
      <q-btn color="positive" label="Update All" icon="sync" @click="updateAllDevices" :loading="loading" class="q-mr-sm" />
      <q-btn color="secondary" label="Scan for Devices" icon="search" @click="startScan" :loading="scanning" />
    </div>

    <!-- Scan Dialog -->
    <q-dialog v-model="scanDialogOpen" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center">
          <q-icon name="search" size="md" color="primary" class="q-mr-sm" />
          <span class="text-h6">Device Scan</span>
        </q-card-section>
        <q-card-section>
          <div v-if="scanning" class="text-center">
            <q-spinner-dots size="40px" color="primary" />
            <div class="q-mt-sm">Scanning for devices... Press button on device to learn.</div>
          </div>
          <div v-else-if="scanResult">
            <div v-if="scanResult.found" class="text-positive">
              <q-icon name="check_circle" /> Device found!
              <div class="q-mt-sm">Address: {{ scanResult.address }}</div>
            </div>
            <div v-else class="text-negative">
              <q-icon name="cancel" /> No device found.
            </div>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-if="scanning" flat label="Stop Scan" color="negative" @click="stopScan" />
          <q-btn v-if="scanResult?.found" flat label="Save Device" color="positive" @click="saveScannedDevice" />
          <q-btn flat label="Close" color="primary" v-close-popup @click="closeScanDialog" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Device Info Dialog -->
    <q-dialog v-model="infoDialogOpen">
      <q-card style="min-width: 500px">
        <q-card-section class="row items-center q-pb-none">
          <span class="text-h6">Device {{ selectedDevice?.id }} Info</span>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section v-if="selectedDeviceInfo">
          <q-list dense>
            <q-item v-for="(value, key) in selectedDeviceInfo" :key="key">
              <q-item-section>
                <q-item-label caption>{{ key }}</q-item-label>
                <q-item-label>{{ value }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Devices Table -->
    <q-table
      flat
      bordered
      :rows="devices"
      :columns="columns"
      row-key="id"
      :loading="loading"
      :pagination="{ rowsPerPage: 20 }"
    >
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">{{ props.row.id }}</q-td>
          <q-td key="name" :props="props">
            <span class="cursor-pointer text-primary" @click="editName(props.row)">
              {{ props.row.name || 'Device-' + props.row.id }}
              <q-icon name="edit" size="xs" class="q-ml-xs" />
            </span>
          </q-td>
          <q-td key="type" :props="props">
            <q-select
              dense
              outlined
              v-model="props.row.deviceType"
              :options="deviceTypes"
              @update:model-value="setDeviceType(props.row.id, $event)"
              style="min-width: 120px"
            />
          </q-td>
          <q-td key="value" :props="props">
            <q-badge :color="props.row.info?.value > 50 ? 'positive' : 'warning'">
              {{ props.row.info?.value ?? '-' }}%
            </q-badge>
          </q-td>
          <q-td key="state" :props="props">
            <q-chip :color="stateColor(props.row.info?.movementState)" text-color="white" size="sm">
              {{ stateLabel(props.row.info?.movementState) }}
            </q-chip>
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs">
              <q-btn dense flat icon="arrow_upward" color="positive" @click="moveDevice(props.row.id, 'up')">
                <q-tooltip>Move Up</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="stop" color="warning" @click="moveDevice(props.row.id, 'stop')">
                <q-tooltip>Stop</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="arrow_downward" color="negative" @click="moveDevice(props.row.id, 'down')">
                <q-tooltip>Move Down</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="looks_one" color="info" @click="moveDevice(props.row.id, 'pos1')">
                <q-tooltip>Position 1</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="looks_two" color="info" @click="moveDevice(props.row.id, 'pos2')">
                <q-tooltip>Position 2</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="info" color="primary" @click="showInfo(props.row)">
                <q-tooltip>Device Info</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="delete" color="negative" @click="confirmDelete(props.row)">
                <q-tooltip>Delete Device</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

const $q = useQuasar()

const devices = ref([])
const loading = ref(false)
const scanning = ref(false)
const scanDialogOpen = ref(false)
const scanResult = ref(null)
const infoDialogOpen = ref(false)
const selectedDevice = ref(null)
const selectedDeviceInfo = ref(null)

const deviceTypes = ['UNKNOWN', 'SHUTTER', 'BLIND', 'AWNING', 'SWITCH', 'DIMMER', 'NIGHT_LIGHT', 'DRAWN_LIGHT', 'HEATING', 'COOLING', 'SWITCHDAY', 'GATEWAY']

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'left' },
  { name: 'type', label: 'Type', field: 'deviceType', align: 'left' },
  { name: 'value', label: 'Value', field: row => row.info?.value, sortable: true, align: 'center' },
  { name: 'state', label: 'State', field: row => row.info?.movementState, align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

function stateLabel(state) {
  const map = { 0: 'Unknown', 1: 'Stopped', 2: 'Up', 3: 'Down' }
  return map[state] ?? 'Unknown'
}

function stateColor(state) {
  const map = { 0: 'grey', 1: 'positive', 2: 'info', 3: 'warning' }
  return map[state] ?? 'grey'
}

async function loadDevices() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/devices')
    devices.value = (Array.isArray(data) ? data : []).map(d => ({
      ...d,
      deviceType: d.info?.type || 'UNKNOWN'
    }))
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load devices', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function updateAllDevices() {
  loading.value = true
  try {
    await axios.post('/api/devices/updateAll')
    $q.notify({ color: 'positive', message: 'All devices updated', icon: 'check' })
    await loadDevices()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to update devices', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function moveDevice(id, action) {
  const endpoint = {
    up: `/api/devices/${id}/moveUp`,
    down: `/api/devices/${id}/moveDown`,
    stop: `/api/devices/${id}/stop`,
    pos1: `/api/devices/${id}/movePos1`,
    pos2: `/api/devices/${id}/movePos2`,
  }[action]
  try {
    await axios.post(endpoint)
    $q.notify({ color: 'positive', message: `Device ${id} ${action}`, icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Command failed', icon: 'error' })
  }
}

async function setDeviceType(id, type) {
  try {
    await axios.post(`/api/devices/${id}/setType`, { type })
    $q.notify({ color: 'positive', message: 'Type updated', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to set type', icon: 'error' })
  }
}

function editName(device) {
  $q.dialog({
    title: 'Rename Device',
    message: 'Enter new name:',
    prompt: { model: device.name || `Device-${device.id}`, type: 'text' },
    cancel: true,
  }).onOk(async name => {
    try {
      await axios.put(`/api/devices/rename/${device.id}`, { name })
      device.name = name
      $q.notify({ color: 'positive', message: 'Device renamed', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to rename', icon: 'error' })
    }
  })
}

function confirmDelete(device) {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete device ${device.name || device.id}?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await axios.delete(`/api/devices/delete/${device.id}`)
      $q.notify({ color: 'positive', message: 'Device deleted', icon: 'check' })
      await loadDevices()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to delete', icon: 'error' })
    }
  })
}

async function showInfo(device) {
  selectedDevice.value = device
  try {
    const { data } = await axios.get(`/api/devices/${device.id}/info`)
    selectedDeviceInfo.value = data
    infoDialogOpen.value = true
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load info', icon: 'error' })
  }
}

// Scan flow
let scanPollInterval = null

async function startScan() {
  scanDialogOpen.value = true
  scanning.value = true
  scanResult.value = null
  try {
    await axios.post('/api/devices/scan/start')
    scanPollInterval = setInterval(pollScanResult, 2000)
  } catch (e) {
    scanning.value = false
    $q.notify({ color: 'negative', message: 'Failed to start scan', icon: 'error' })
  }
}

async function pollScanResult() {
  try {
    const { data } = await axios.get('/api/devices/scan/result')
    if (data && (data.found || data.finished)) {
      clearInterval(scanPollInterval)
      scanning.value = false
      scanResult.value = data
    }
  } catch (e) {
    // continue polling
  }
}

async function stopScan() {
  clearInterval(scanPollInterval)
  try {
    await axios.post('/api/devices/scan/stop')
  } catch (e) {
    // ignore
  }
  scanning.value = false
}

async function saveScannedDevice() {
  try {
    await axios.post('/api/devices/save')
    $q.notify({ color: 'positive', message: 'Device saved', icon: 'check' })
    scanDialogOpen.value = false
    await loadDevices()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to save device', icon: 'error' })
  }
}

function closeScanDialog() {
  if (scanning.value) stopScan()
  scanResult.value = null
}

onMounted(loadDevices)
</script>

<style scoped>
</style>
