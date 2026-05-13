<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Settings</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadAll" :loading="loading" />
    </div>

    <div class="row q-gutter-md">
      <!-- RF Settings -->
      <div class="col-12 col-md-5">
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">RF Network Settings</div>
            <q-banner class="bg-orange-1 q-mb-md" rounded dense>
              <template v-slot:avatar><q-icon name="warning" color="orange" size="sm" /></template>
              Changing RF settings may disconnect devices. Only change if you know what you are doing.
            </q-banner>
            <div class="q-gutter-md">
              <q-input v-model.number="rfSettings.address" type="number" label="Net Address" outlined dense />
              <q-input v-model.number="rfSettings.resetCount" type="number" label="Reset Counter" outlined dense />
              <q-btn color="primary" label="Apply RF Settings" icon="save" @click="applyRFSettings" :loading="savingRF" />
            </div>
          </q-card-section>
        </q-card>

        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Duty Cycle Mode</div>
            <q-btn-toggle
              v-model="dutyMode"
              toggle-color="primary"
              :options="[{label: 'Normal', value: 0}, {label: 'Extended', value: 1}]"
              @update:model-value="setDutyMode"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- About -->
      <div class="col-12 col-md-6">
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">About Selve Configurator</div>
            <q-list dense>
              <q-item>
                <q-item-section avatar><q-icon name="info" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>Application</q-item-label>
                  <q-item-label>Selve Configurator for Home Assistant</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="code" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>Protocol</q-item-label>
                  <q-item-label>Selve XML-RPC over Home Assistant Services</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="description" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>XML Specification</q-item-label>
                  <q-item-label>Rev. 2.0.2</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Feature Support</div>
            <q-list dense separator>
              <q-item v-for="feat in features" :key="feat.name">
                <q-item-section avatar>
                  <q-icon :name="feat.icon" :color="feat.available ? 'positive' : 'grey'" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ feat.name }}</q-item-label>
                  <q-item-label caption>{{ feat.description }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge :color="feat.available ? 'positive' : 'orange'">
                    {{ feat.available ? 'Available' : 'Needs HA Service' }}
                  </q-badge>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

const $q = useQuasar()
const loading = ref(false)
const savingRF = ref(false)
const dutyMode = ref(0)
const rfSettings = reactive({ address: 0, resetCount: 0 })

const features = [
  { name: 'Commeo Devices', icon: 'blinds', description: 'Full device control, scan, teach, manual write', available: true },
  { name: 'Iveo Devices', icon: 'cast', description: 'Iveo control, teach, learn, repeater', available: true },
  { name: 'Groups', icon: 'group_work', description: 'Group management and control', available: true },
  { name: 'Sensors', icon: 'sensors', description: 'Sensor management and values', available: true },
  { name: 'Senders', icon: 'settings_remote', description: 'Sender management and teach', available: true },
  { name: 'Gateway Config', icon: 'router', description: 'LED, events, forwarding, resets', available: true },
  { name: 'Sensor Simulation', icon: 'science', description: 'Virtual sensor simulation', available: true },
  { name: 'Firmware Update', icon: 'system_update', description: 'Gateway firmware version and update', available: true },
  { name: 'Position Save', icon: 'save', description: 'Save current position as Pos1/Pos2', available: true },
  { name: 'Forced Commands', icon: 'priority_high', description: 'Bypass sensor safety locks', available: true },
  { name: 'XML Log', icon: 'code', description: 'View communication protocol log', available: true },
]

async function loadAll() {
  loading.value = true
  try {
    const [rfRes, dutyRes] = await Promise.all([
      axios.get('/api/gateway/rf').catch(() => ({ data: {} })),
      axios.get('/api/gateway/duty').catch(() => ({ data: {} })),
    ])
    const rf = rfRes.data || {}
    rfSettings.address = rf.netAddress ?? rf.address ?? 0
    rfSettings.resetCount = rf.resetCount ?? 0
    dutyMode.value = dutyRes.data?.dutyMode ?? 0
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load settings', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function applyRFSettings() {
  savingRF.value = true
  try {
    await axios.post('/api/gateway/setRF', rfSettings)
    $q.notify({ color: 'positive', message: 'RF settings applied', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to apply RF settings', icon: 'error' })
  } finally {
    savingRF.value = false
  }
}

async function setDutyMode(mode) {
  try {
    await axios.post('/api/gateway/setDuty', { mode })
    $q.notify({ color: 'positive', message: 'Duty mode updated', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to set duty mode', icon: 'error' })
  }
}

onMounted(loadAll)
</script>
