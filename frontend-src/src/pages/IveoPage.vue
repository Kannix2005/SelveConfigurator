<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Iveo Devices</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadIveoDevices" :loading="loading" class="q-mr-sm" />
      <q-btn color="secondary" label="Teach Iveo" icon="school" @click="teachIveo" :loading="teaching" class="q-mr-sm" />
      <q-btn color="accent" label="Learn" icon="cast_connected" @click="learnIveo" :loading="learning" />
    </div>

    <!-- Repeater Settings -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="row items-center">
          <div class="text-subtitle1">Repeater Mode</div>
          <q-space />
          <q-btn-toggle
            v-model="repeaterLevel"
            toggle-color="primary"
            :options="[
              {label: 'Off', value: 0},
              {label: 'Single', value: 1},
              {label: 'Multi', value: 2}
            ]"
            @update:model-value="setRepeater"
          />
        </div>
      </q-card-section>
    </q-card>

    <!-- Iveo Devices Table -->
    <q-table
      flat
      bordered
      :rows="iveoDevices"
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
              {{ props.row.name || 'Iveo-' + props.row.id }}
              <q-icon name="edit" size="xs" class="q-ml-xs" />
            </span>
          </q-td>
          <q-td key="type" :props="props">
            <q-select
              dense
              outlined
              v-model="props.row.type"
              :options="iveoTypes"
              @update:model-value="setType(props.row.id, $event)"
              style="min-width: 120px"
            />
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs">
              <q-btn dense flat icon="arrow_upward" color="positive" @click="commandManual(props.row.id, 'UP')">
                <q-tooltip>Up</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="stop" color="warning" @click="commandManual(props.row.id, 'STOP')">
                <q-tooltip>Stop</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="arrow_downward" color="negative" @click="commandManual(props.row.id, 'DOWN')">
                <q-tooltip>Down</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="looks_one" color="info" @click="commandManual(props.row.id, 'POS1')">
                <q-tooltip>Position 1</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="looks_two" color="info" @click="commandManual(props.row.id, 'POS2')">
                <q-tooltip>Position 2</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </q-tr>
      </template>

      <template v-slot:no-data>
        <div class="full-width row flex-center text-grey q-gutter-sm">
          <q-icon name="cast" size="md" />
          <span>No Iveo devices found. Use "Teach" or "Learn" to add one.</span>
        </div>
      </template>
    </q-table>

    <!-- Factory Reset -->
    <q-card flat bordered class="q-mt-md bg-red-1">
      <q-card-section>
        <div class="row items-center">
          <div>
            <div class="text-subtitle1 text-negative">Factory Reset Iveo Channel</div>
            <div class="text-caption">This will delete all learned Iveo devices.</div>
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

const iveoDevices = ref([])
const loading = ref(false)
const teaching = ref(false)
const learning = ref(false)
const repeaterLevel = ref(0)

const iveoTypes = ['UNKNOWN', 'SHUTTER', 'BLIND', 'AWNING', 'SWITCH', 'DIMMER', 'NIGHT_LIGHT', 'DRAWN_LIGHT', 'HEATING', 'COOLING', 'SWITCHDAY', 'GATEWAY']

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'left' },
  { name: 'type', label: 'Type', field: 'type', align: 'left' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

async function loadIveoDevices() {
  loading.value = true
  try {
    const [devRes, repRes] = await Promise.all([
      axios.get('/api/iveo'),
      axios.get('/api/iveo/getRepeater'),
    ])
    iveoDevices.value = Array.isArray(devRes.data) ? devRes.data : []
    const rs = repRes.data?.repeater_state
    if (rs === 'NONE' || rs === 0) repeaterLevel.value = 0
    else if (rs === 'SINGLEREPEAT' || rs === 1) repeaterLevel.value = 1
    else repeaterLevel.value = 2
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load Iveo devices', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function setRepeater(level) {
  try {
    await axios.post('/api/iveo/setRepeater', { level })
    $q.notify({ color: 'positive', message: 'Repeater mode updated', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to set repeater', icon: 'error' })
  }
}

async function setType(id, type) {
  try {
    await axios.post(`/api/iveo/${id}/setType`, { type })
    $q.notify({ color: 'positive', message: 'Type updated', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to set type', icon: 'error' })
  }
}

function editLabel(device) {
  $q.dialog({
    title: 'Rename Iveo Device',
    message: 'Enter new label:',
    prompt: { model: device.name || `Iveo-${device.id}`, type: 'text' },
    cancel: true,
  }).onOk(async label => {
    try {
      await axios.put(`/api/iveo/${device.id}/setLabel`, { label })
      device.name = label
      $q.notify({ color: 'positive', message: 'Device renamed', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to rename', icon: 'error' })
    }
  })
}

async function commandManual(id, command) {
  const cmdMap = { STOP: 0, UP: 1, DOWN: 2, POS1: 3, POS2: 4 }
  try {
    await axios.post(`/api/iveo/${id}/commandManual`, { commandType: cmdMap[command] ?? 0 })
    $q.notify({ color: 'positive', message: `Command ${command} sent`, icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Command failed', icon: 'error' })
  }
}

async function teachIveo() {
  teaching.value = true
  $q.dialog({
    title: 'Iveo Teach',
    message: 'This will send a teach telegram. Put the target device into learn mode first, then click OK.',
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      const id = iveoDevices.value[0]?.id ?? 0
      await axios.post(`/api/iveo/${id}/teach`)
      $q.notify({ color: 'positive', message: 'Teach telegram sent', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Teach failed', icon: 'error' })
    } finally {
      teaching.value = false
    }
  }).onCancel(() => {
    teaching.value = false
  })
}

async function learnIveo() {
  learning.value = true
  $q.dialog({
    title: 'Iveo Learn',
    message: 'This will put the gateway into learn mode. Send a teach telegram from your remote or device, then click OK.',
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      // Use first available ID or 0
      const id = iveoDevices.value[0]?.id ?? 0
      await axios.post(`/api/iveo/${id}/learn`)
      $q.notify({ color: 'positive', message: 'Learn mode activated', icon: 'check' })
      await loadIveoDevices()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Learn failed', icon: 'error' })
    } finally {
      learning.value = false
    }
  }).onCancel(() => {
    learning.value = false
  })
}

function confirmFactoryReset() {
  $q.dialog({
    title: 'Factory Reset Iveo',
    message: 'This will delete ALL learned Iveo devices. Are you sure?',
    cancel: true,
    persistent: true,
    ok: { label: 'Reset', color: 'negative' },
  }).onOk(async () => {
    try {
      const id = iveoDevices.value[0]?.id ?? 0
      await axios.post(`/api/iveo/${id}/factoryReset`)
      $q.notify({ color: 'positive', message: 'Iveo factory reset complete', icon: 'check' })
      await loadIveoDevices()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Factory reset failed', icon: 'error' })
    }
  })
}

onMounted(loadIveoDevices)
</script>

<style scoped>
</style>
