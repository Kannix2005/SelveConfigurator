<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Firmware Management</div>
      <q-space />
      <q-btn color="primary" label="Refresh Version" icon="refresh" @click="loadFirmwareVersion" :loading="loading" />
    </div>

    <!-- Current Firmware Info -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-subtitle1 q-mb-sm">Current Firmware</div>
        <q-list dense>
          <q-item>
            <q-item-section avatar>
              <q-icon name="memory" color="primary" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Firmware Version</q-item-label>
              <q-item-label caption>{{ firmwareVersion || 'Loading...' }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section avatar>
              <q-icon name="developer_board" color="primary" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Gateway State</q-item-label>
              <q-item-label caption>
                <q-badge :color="gatewayState === 'READY' ? 'positive' : 'warning'">
                  {{ gatewayState || 'Unknown' }}
                </q-badge>
              </q-item-label>
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section avatar>
              <q-icon name="thermostat" color="orange" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Module Temperature</q-item-label>
              <q-item-label caption>{{ temperature !== null ? temperature + '°C' : 'N/A' }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
    </q-card>

    <!-- Firmware Upload -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-subtitle1 q-mb-sm">Firmware Update</div>
        <q-banner class="bg-orange-1 q-mb-md" rounded>
          <template v-slot:avatar>
            <q-icon name="warning" color="orange" />
          </template>
          <strong>Warning:</strong> Firmware updates can take several minutes. Do NOT disconnect the gateway 
          or power during the update process. An incorrect firmware file may brick the gateway.
        </q-banner>

        <q-file
          v-model="firmwareFile"
          outlined
          label="Select firmware file (.aes)"
          accept=".aes,.bin,.hex"
          class="q-mb-md"
        >
          <template v-slot:prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>

        <div v-if="uploading" class="q-mb-md">
          <q-linear-progress :value="uploadProgress" color="primary" class="q-mb-sm" />
          <div class="text-caption text-center">{{ uploadStatusText }}</div>
        </div>

        <div class="row q-gutter-sm">
          <q-btn
            color="primary"
            label="Upload & Update Firmware"
            icon="system_update"
            :disable="!firmwareFile || uploading"
            :loading="uploading"
            @click="confirmUpload"
          />
        </div>
      </q-card-section>
    </q-card>

    <!-- Gateway Ping -->
    <q-card flat bordered>
      <q-card-section>
        <div class="text-subtitle1 q-mb-sm">Gateway Connection Test</div>
        <div class="row items-center q-gutter-md">
          <q-btn color="info" label="Ping Gateway" icon="network_ping" @click="pingGateway" :loading="pinging" />
          <span v-if="pingResult !== null">
            <q-badge :color="pingResult ? 'positive' : 'negative'">
              {{ pingResult ? 'Gateway reachable' : 'Gateway not responding' }}
            </q-badge>
          </span>
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

const loading = ref(false)
const firmwareVersion = ref('')
const gatewayState = ref('')
const temperature = ref(null)
const firmwareFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatusText = ref('')
const pinging = ref(false)
const pingResult = ref(null)

async function loadFirmwareVersion() {
  loading.value = true
  try {
    const [fwRes, stateRes, tempRes] = await Promise.all([
      axios.get('/api/firmware/version').catch(() => ({ data: {} })),
      axios.get('/api/gateway/state').catch(() => ({ data: {} })),
      axios.get('/api/gateway/temperature').catch(() => ({ data: {} })),
    ])
    firmwareVersion.value = fwRes.data?.version || fwRes.data?.state || 'Unknown'
    gatewayState.value = stateRes.data?.state || 'Unknown'
    temperature.value = tempRes.data?.temperature ?? null
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load firmware info', icon: 'error' })
  } finally {
    loading.value = false
  }
}

function confirmUpload() {
  $q.dialog({
    title: 'Confirm Firmware Update',
    message: 'Are you sure you want to upload and apply this firmware? The gateway will restart and be unavailable during the update.',
    cancel: true,
    persistent: true,
    ok: { label: 'Update', color: 'warning' },
  }).onOk(() => uploadFirmware())
}

async function uploadFirmware() {
  if (!firmwareFile.value) return
  uploading.value = true
  uploadProgress.value = 0
  uploadStatusText.value = 'Reading firmware file...'

  try {
    const formData = new FormData()
    formData.append('firmware', firmwareFile.value)

    uploadStatusText.value = 'Uploading firmware...'
    uploadProgress.value = 0.3

    const { data } = await axios.post('/api/firmware/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total) {
          uploadProgress.value = 0.3 + (e.loaded / e.total) * 0.5
        }
      }
    })

    uploadProgress.value = 1
    uploadStatusText.value = 'Firmware update complete!'
    $q.notify({ color: 'positive', message: 'Firmware updated successfully', icon: 'check_circle' })

    // Reload version after update
    setTimeout(() => loadFirmwareVersion(), 5000)
  } catch (e) {
    const errMsg = e.response?.data?.error || e.message
    $q.notify({ color: 'negative', message: `Firmware update failed: ${errMsg}`, icon: 'error' })
    uploadStatusText.value = 'Update failed!'
  } finally {
    uploading.value = false
  }
}

async function pingGateway() {
  pinging.value = true
  pingResult.value = null
  try {
    const { data } = await axios.get('/api/gateway/ping')
    pingResult.value = !data.error
  } catch (e) {
    pingResult.value = false
  } finally {
    pinging.value = false
  }
}

onMounted(loadFirmwareVersion)
</script>

<style scoped>
</style>
