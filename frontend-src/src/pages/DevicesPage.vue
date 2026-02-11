<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Devices (Actors)</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadDevices" :loading="loading" class="q-mr-sm" />
      <q-btn color="positive" label="Update All" icon="sync" @click="updateAllDevices" :loading="loading" class="q-mr-sm" />
      <q-btn color="secondary" label="Scan for Devices" icon="search" @click="startScan" :loading="scanning" class="q-mr-sm" />
      <q-btn color="accent" label="Write Manual" icon="edit_note" @click="openManualWriteDialog" />
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

    <!-- Manual Write Dialog -->
    <q-dialog v-model="manualWriteDialogOpen" persistent>
      <q-card style="min-width: 450px">
        <q-card-section>
          <span class="text-h6">Write Manual Device</span>
        </q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model.number="manualDevice.id" label="Device ID (0-63)" type="number" outlined />
          <q-input v-model="manualDevice.address" label="RF Address" outlined />
          <q-input v-model="manualDevice.name" label="Device Name" outlined />
          <q-select v-model="manualDevice.type" :options="deviceTypes" label="Device Type" outlined />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Write" color="primary" @click="writeManualDevice" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Device Detail Dialog -->
    <q-dialog v-model="detailDialogOpen" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card v-if="selectedDevice">
        <q-bar class="bg-primary text-white">
          <span>Device {{ selectedDevice.id }}: {{ selectedDevice.name || 'Unnamed' }}</span>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup />
        </q-bar>
        <q-card-section class="q-pa-md">
          <div class="row q-gutter-lg">
            <!-- Left: Info -->
            <div class="col-12 col-md-5">
              <q-list bordered separator class="rounded-borders">
                <q-item-label header>Device Information</q-item-label>
                <q-item v-for="(value, key) in selectedDeviceInfo" :key="key">
                  <q-item-section>
                    <q-item-label caption>{{ key }}</q-item-label>
                    <q-item-label>{{ formatValue(value) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
              <q-list bordered separator class="rounded-borders q-mt-md" v-if="selectedDeviceValues">
                <q-item-label header>Current Values</q-item-label>
                <q-item v-for="(value, key) in selectedDeviceValues" :key="key">
                  <q-item-section>
                    <q-item-label caption>{{ key }}</q-item-label>
                    <q-item-label>{{ formatValue(value) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
            <!-- Right: Controls -->
            <div class="col-12 col-md-6">
              <q-card flat bordered class="q-mb-md">
                <q-card-section>
                  <div class="text-subtitle1 q-mb-sm">Movement Controls</div>
                  <div class="row q-gutter-sm q-mb-md">
                    <q-btn icon="arrow_upward" color="positive" label="Up" @click="moveDevice(selectedDevice.id, 'up')" />
                    <q-btn icon="stop" color="warning" label="Stop" @click="moveDevice(selectedDevice.id, 'stop')" />
                    <q-btn icon="arrow_downward" color="negative" label="Down" @click="moveDevice(selectedDevice.id, 'down')" />
                  </div>
                  <div class="row q-gutter-sm q-mb-md">
                    <q-btn icon="looks_one" color="info" label="Pos 1" @click="moveDevice(selectedDevice.id, 'pos1')" />
                    <q-btn icon="looks_two" color="info" label="Pos 2" @click="moveDevice(selectedDevice.id, 'pos2')" />
                  </div>
                  <div class="text-subtitle2 q-mb-xs">Target Position (0-100%)</div>
                  <div class="row items-center q-gutter-sm q-mb-md">
                    <q-slider v-model="positionSlider" :min="0" :max="100" label class="col" />
                    <q-btn flat color="primary" label="Go" @click="moveToPosition(selectedDevice.id)" />
                  </div>
                </q-card-section>
              </q-card>

              <q-card flat bordered class="q-mb-md">
                <q-card-section>
                  <div class="text-subtitle1 q-mb-sm">Save Positions</div>
                  <div class="text-caption q-mb-sm">Save the current device position as a preset.</div>
                  <div class="row q-gutter-sm">
                    <q-btn icon="save" color="teal" label="Save as Pos 1" @click="savePosition(selectedDevice.id, 1)" />
                    <q-btn icon="save" color="teal" label="Save as Pos 2" @click="savePosition(selectedDevice.id, 2)" />
                  </div>
                </q-card-section>
              </q-card>

              <q-card flat bordered class="q-mb-md bg-orange-1">
                <q-card-section>
                  <div class="text-subtitle1 q-mb-sm">Forced Commands</div>
                  <div class="text-caption q-mb-sm">Bypasses wind/rain sensor safety locks.</div>
                  <div class="row q-gutter-sm">
                    <q-btn icon="arrow_upward" color="orange" label="Force Up" @click="forcedMove(selectedDevice.id, 'up')" />
                    <q-btn icon="stop" color="orange" label="Force Stop" @click="forcedMove(selectedDevice.id, 'stop')" />
                    <q-btn icon="arrow_downward" color="orange" label="Force Down" @click="forcedMove(selectedDevice.id, 'down')" />
                  </div>
                </q-card-section>
              </q-card>

              <q-card flat bordered>
                <q-card-section>
                  <div class="text-subtitle1 q-mb-sm">Configuration</div>
                  <div class="row q-gutter-md">
                    <q-select v-model="selectedDeviceType" :options="deviceTypes" label="Device Type" outlined dense style="min-width: 160px"
                      @update:model-value="setDeviceType(selectedDevice.id, selectedDevice.communicationType, $event)" />
                    <q-select v-model="selectedDeviceFunction" :options="deviceFunctions" label="Function" outlined dense style="min-width: 160px"
                      @update:model-value="setDeviceFunction(selectedDevice.id, $event)" />
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Devices Table -->
    <q-table flat bordered :rows="devices" :columns="columns" row-key="id" :loading="loading"
      :pagination="{ rowsPerPage: 20 }" :filter="tableFilter">
      <template v-slot:top-right>
        <q-input dense debounce="300" v-model="tableFilter" placeholder="Search...">
          <template v-slot:append><q-icon name="search" /></template>
        </q-input>
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer" @click="showDetail(props.row)">
          <q-td key="id" :props="props">{{ props.row.id }}</q-td>
          <q-td key="name" :props="props">
            <span class="text-primary" @click.stop="editName(props.row)">
              {{ props.row.name || 'Device-' + props.row.id }}
              <q-icon name="edit" size="xs" class="q-ml-xs" />
            </span>
          </q-td>
          <q-td key="communication" :props="props">
            <q-chip :color="props.row.communicationType === 'IVEO' ? 'secondary' : 'primary'" text-color="white" size="sm">
              {{ props.row.communicationType || 'COMMEO' }}
            </q-chip>
          </q-td>
          <q-td key="type" :props="props">
            <q-select dense outlined v-model="props.row.deviceType" :options="deviceTypes"
              @update:model-value="setDeviceType(props.row.id, props.row.communicationType, $event)"
              @click.stop style="min-width: 120px" />
          </q-td>
          <q-td key="value" :props="props">
            <q-badge :color="(props.row.info?.value ?? 0) > 50 ? 'positive' : 'warning'">
              {{ props.row.info?.value ?? '-' }}%
            </q-badge>
          </q-td>
          <q-td key="state" :props="props">
            <q-chip :color="stateColor(props.row.info?.movementState)" text-color="white" size="sm">
              {{ stateLabel(props.row.info?.movementState) }}
            </q-chip>
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs" @click.stop>
              <q-btn dense flat icon="arrow_upward" color="positive" @click="moveDevice(props.row.id, 'up')"><q-tooltip>Up</q-tooltip></q-btn>
              <q-btn dense flat icon="stop" color="warning" @click="moveDevice(props.row.id, 'stop')"><q-tooltip>Stop</q-tooltip></q-btn>
              <q-btn dense flat icon="arrow_downward" color="negative" @click="moveDevice(props.row.id, 'down')"><q-tooltip>Down</q-tooltip></q-btn>
              <q-btn dense flat icon="looks_one" color="info" @click="moveDevice(props.row.id, 'pos1')"><q-tooltip>Pos 1</q-tooltip></q-btn>
              <q-btn dense flat icon="looks_two" color="info" @click="moveDevice(props.row.id, 'pos2')"><q-tooltip>Pos 2</q-tooltip></q-btn>
              <q-btn dense flat icon="open_in_full" color="primary" @click="showDetail(props.row)"><q-tooltip>Details</q-tooltip></q-btn>
              <q-btn dense flat icon="delete" color="negative" @click="confirmDelete(props.row)"><q-tooltip>Delete</q-tooltip></q-btn>
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
const tableFilter = ref('')
const detailDialogOpen = ref(false)
const selectedDevice = ref(null)
const selectedDeviceInfo = ref(null)
const selectedDeviceValues = ref(null)
const selectedDeviceType = ref('UNKNOWN')
const selectedDeviceFunction = ref('SELECT')
const positionSlider = ref(50)
const manualWriteDialogOpen = ref(false)
const manualDevice = ref({ id: 0, address: '', name: '', type: 'UNKNOWN' })

const deviceTypes = ['UNKNOWN', 'SHUTTER', 'BLIND', 'AWNING', 'SWITCH', 'DIMMER', 'NIGHT_LIGHT', 'DRAWN_LIGHT', 'HEATING', 'COOLING', 'SWITCHDAY', 'GATEWAY']
const deviceFunctions = ['SELECT', 'DRIVE', 'VENTILATION', 'SUN', 'NIGHTCLOSE', 'SAVE1', 'SAVE2']

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'left' },
  { name: 'communication', label: 'Comm', field: 'communicationType', sortable: true, align: 'center' },
  { name: 'type', label: 'Type', field: 'deviceType', align: 'left' },
  { name: 'value', label: 'Position', field: row => row.info?.value, sortable: true, align: 'center' },
  { name: 'state', label: 'State', field: row => row.info?.movementState, align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

function stateLabel(s) { return { 0:'Unknown', 1:'Stopped', 2:'Moving Up', 3:'Moving Down' }[s] ?? 'Unknown' }
function stateColor(s) { return { 0:'grey', 1:'positive', 2:'info', 3:'warning' }[s] ?? 'grey' }
function formatValue(v) { if (v == null) return '-'; if (typeof v === 'object') return JSON.stringify(v); return String(v) }

async function loadDevices() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/devices')
    devices.value = (Array.isArray(data) ? data : []).map(d => ({
      ...d, deviceType: d.deviceType || d.type || 'UNKNOWN', communicationType: d.communicationType || 'COMMEO'
    }))
  } catch (e) { $q.notify({ color: 'negative', message: 'Failed to load devices', icon: 'error' }) }
  finally { loading.value = false }
}

async function updateAllDevices() {
  loading.value = true
  try { await axios.post('/api/devices/updateAll'); $q.notify({ color: 'positive', message: 'All devices updated', icon: 'check' }); await loadDevices() }
  catch (e) { $q.notify({ color: 'negative', message: 'Update failed', icon: 'error' }) }
  finally { loading.value = false }
}

async function moveDevice(id, action) {
  const ep = { up: 'moveUp', down: 'moveDown', stop: 'stop', pos1: 'movePos1', pos2: 'movePos2' }[action]
  try { await axios.post(`/api/devices/${id}/${ep}`); $q.notify({ color: 'positive', message: `${action}`, icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Command failed', icon: 'error' }) }
}

async function moveToPosition(id) {
  try { await axios.post(`/api/devices/${id}/movePos`, { position: positionSlider.value }); $q.notify({ color: 'positive', message: `Moving to ${positionSlider.value}%`, icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Position failed', icon: 'error' }) }
}

async function savePosition(id, num) {
  try { await axios.post(`/api/devices/${id}/savePos${num}`); $q.notify({ color: 'positive', message: `Pos ${num} saved`, icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Save failed', icon: 'error' }) }
}

async function forcedMove(id, action) {
  const ep = { up: 'moveUpForced', down: 'moveDownForced', stop: 'stopForced' }[action]
  try { await axios.post(`/api/devices/${id}/${ep}`); $q.notify({ color: 'positive', message: `Forced ${action}`, icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Forced command failed', icon: 'error' }) }
}

async function setDeviceType(id, comm, type) {
  try { const ep = comm === 'IVEO' ? `/api/iveo/${id}/setType` : `/api/devices/${id}/setType`; await axios.post(ep, { type }); $q.notify({ color: 'positive', message: 'Type updated', icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Failed', icon: 'error' }) }
}

async function setDeviceFunction(id, func) {
  try { await axios.post(`/api/devices/${id}/setFunction`, { function: func }); $q.notify({ color: 'positive', message: 'Function set', icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Failed', icon: 'error' }) }
}

function editName(device) {
  $q.dialog({ title: 'Rename Device', message: 'Enter new name:', prompt: { model: device.name || `Device-${device.id}`, type: 'text' }, cancel: true })
  .onOk(async name => {
    try {
      const ep = device.communicationType === 'IVEO' ? `/api/iveo/${device.id}/setLabel` : `/api/devices/rename/${device.id}`
      const payload = device.communicationType === 'IVEO' ? { label: name } : { name }
      await axios.put(ep, payload); device.name = name; $q.notify({ color: 'positive', message: 'Renamed', icon: 'check' })
    } catch (e) { $q.notify({ color: 'negative', message: 'Rename failed', icon: 'error' }) }
  })
}

function confirmDelete(device) {
  $q.dialog({ title: 'Confirm Delete', message: `Delete "${device.name || device.id}"?`, cancel: true, persistent: true, ok: { label: 'Delete', color: 'negative' } })
  .onOk(async () => {
    try { await axios.delete(`/api/devices/delete/${device.id}`); $q.notify({ color: 'positive', message: 'Deleted', icon: 'check' }); await loadDevices() }
    catch (e) { $q.notify({ color: 'negative', message: 'Delete failed', icon: 'error' }) }
  })
}

async function showDetail(device) {
  selectedDevice.value = device; selectedDeviceType.value = device.deviceType || 'UNKNOWN'
  selectedDeviceFunction.value = 'SELECT'; positionSlider.value = device.info?.value ?? 50
  try {
    const [i, v] = await Promise.all([axios.get(`/api/devices/${device.id}/info`), axios.get(`/api/devices/${device.id}/values`)])
    selectedDeviceInfo.value = i.data; selectedDeviceValues.value = v.data; detailDialogOpen.value = true
  } catch (e) { $q.notify({ color: 'negative', message: 'Failed to load details', icon: 'error' }) }
}

function openManualWriteDialog() { manualDevice.value = { id: 0, address: '', name: '', type: 'UNKNOWN' }; manualWriteDialogOpen.value = true }

async function writeManualDevice() {
  try { await axios.post('/api/devices/writeManual', manualDevice.value); $q.notify({ color: 'positive', message: 'Written', icon: 'check' }); manualWriteDialogOpen.value = false; await loadDevices() }
  catch (e) { $q.notify({ color: 'negative', message: 'Write failed', icon: 'error' }) }
}

let scanPollInterval = null

async function startScan() {
  scanDialogOpen.value = true; scanning.value = true; scanResult.value = null
  try { await axios.post('/api/devices/scan/start'); scanPollInterval = setInterval(pollScanResult, 2000) }
  catch (e) { scanning.value = false; $q.notify({ color: 'negative', message: 'Scan failed', icon: 'error' }) }
}

async function pollScanResult() {
  try { const { data } = await axios.get('/api/devices/scan/result'); if (data && (data.found || data.finished)) { clearInterval(scanPollInterval); scanning.value = false; scanResult.value = data } }
  catch (e) { /* poll */ }
}

async function stopScan() { clearInterval(scanPollInterval); try { await axios.post('/api/devices/scan/stop') } catch(e) {} scanning.value = false }

async function saveScannedDevice() {
  try { await axios.post('/api/devices/save'); $q.notify({ color: 'positive', message: 'Saved', icon: 'check' }); scanDialogOpen.value = false; await loadDevices() }
  catch (e) { $q.notify({ color: 'negative', message: 'Save failed', icon: 'error' }) }
}

function closeScanDialog() { if (scanning.value) stopScan(); scanResult.value = null }

onMounted(loadDevices)
</script>
