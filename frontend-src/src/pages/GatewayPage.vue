<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Gateway</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadGatewayData" :loading="loading" />
    </div>

    <div class="row q-gutter-md">
      <!-- Left Column: Status -->
      <div class="col-12 col-md-5">
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Gateway Status</div>
            <q-list dense separator>
              <q-item>
                <q-item-section avatar><q-icon name="tag" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>Firmware Version</q-item-label>
                  <q-item-label>{{ gw.version || '-' }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="fingerprint" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>Serial Number</q-item-label>
                  <q-item-label>{{ gw.serial || '-' }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="info" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>Spec / State</q-item-label>
                  <q-item-label>{{ gw.spec || '-' }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="thermostat" color="orange" /></q-item-section>
                <q-item-section>
                  <q-item-label caption>Module Temperature</q-item-label>
                  <q-item-label>{{ gw.temperature !== null ? gw.temperature + '°C' : 'N/A' }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- Duty Cycle -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Duty Cycle</div>
            <q-list dense separator>
              <q-item v-for="(val, key) in gw.duty" :key="key">
                <q-item-section>
                  <q-item-label caption>{{ key }}</q-item-label>
                  <q-item-label>{{ formatValue(val) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="!gw.duty || Object.keys(gw.duty).length === 0">
                <q-item-section class="text-grey">No duty cycle data</q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- RF Information -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">RF Information</div>
            <q-list dense separator>
              <q-item v-for="(val, key) in gw.rf" :key="key">
                <q-item-section>
                  <q-item-label caption>{{ key }}</q-item-label>
                  <q-item-label>{{ formatValue(val) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="!gw.rf || Object.keys(gw.rf).length === 0">
                <q-item-section class="text-grey">No RF data</q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- Right Column: Functions -->
      <div class="col-12 col-md-6">
        <!-- LED Control -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center">
              <div>
                <div class="text-subtitle1">LED Mode</div>
                <div class="text-caption">Enable or disable the gateway status LEDs</div>
              </div>
              <q-space />
              <q-toggle v-model="ledState" color="blue" @update:model-value="setLED" />
            </div>
          </q-card-section>
        </q-card>

        <!-- Events -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Event Configuration</div>
            <div class="row q-gutter-md">
              <q-toggle v-model="events.log" label="Log Events" color="primary" @update:model-value="setEvents" />
              <q-toggle v-model="events.device" label="Device Events" color="primary" @update:model-value="setEvents" />
              <q-toggle v-model="events.sensor" label="Sensor Events" color="primary" @update:model-value="setEvents" />
              <q-toggle v-model="events.sender" label="Sender Events" color="primary" @update:model-value="setEvents" />
              <q-toggle v-model="events.duty" label="Duty Events" color="primary" @update:model-value="setEvents" />
            </div>
          </q-card-section>
        </q-card>

        <!-- Forwarding/Repeater -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center">
              <div>
                <div class="text-subtitle1">RF Forwarding / Repeater</div>
                <div class="text-caption">Enable the gateway to forward/repeat RF commands</div>
              </div>
              <q-space />
              <q-toggle v-model="forwardingState" color="primary" @update:model-value="setForwarding" />
            </div>
          </q-card-section>
        </q-card>

        <!-- Connection Test -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center q-gutter-md">
              <div>
                <div class="text-subtitle1">Connection Test</div>
                <div class="text-caption">Ping the gateway to verify connection</div>
              </div>
              <q-space />
              <q-btn color="info" label="Ping" icon="network_ping" @click="ping" :loading="pinging" />
              <q-badge v-if="pingResult !== null" :color="pingResult ? 'positive' : 'negative'">
                {{ pingResult ? 'OK' : 'FAIL' }}
              </q-badge>
            </div>
          </q-card-section>
        </q-card>

        <!-- Reset Controls -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle1 q-mb-sm">Gateway Controls</div>
            <div class="row q-gutter-sm">
              <q-btn color="amber" label="Reset Gateway" icon="restart_alt" @click="resetGateway" />
            </div>
          </q-card-section>
        </q-card>

        <!-- Danger Zone -->
        <q-card flat bordered class="bg-red-1">
          <q-card-section>
            <div class="text-subtitle1 text-negative q-mb-sm">Danger Zone</div>
            <div class="row q-gutter-sm">
              <q-btn color="red" label="Factory Reset Iveo" icon="warning" @click="iveoFactory" />
              <q-btn color="red" label="Factory Reset Gateway" icon="dangerous" @click="factoryReset">
                <q-tooltip>Deletes ALL devices!</q-tooltip>
              </q-btn>
            </div>
            <div class="text-caption text-negative q-mt-sm">Factory reset will delete all configured devices, groups, and settings!</div>
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
const ledState = ref(true)
const forwardingState = ref(false)
const pinging = ref(false)
const pingResult = ref(null)
const events = reactive({ log: true, device: true, sensor: false, sender: false, duty: true })
const gw = reactive({ version: '', serial: '', spec: '', temperature: null, duty: {}, rf: {} })

function formatValue(val) {
  if (val == null) return '-'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

async function loadGatewayData() {
  loading.value = true
  try {
    const [gwRes, ledRes, evtRes, fwdRes, tempRes] = await Promise.all([
      axios.get('/api/gatewayData').catch(() => ({ data: {} })),
      axios.get('/api/gateway/led').catch(() => ({ data: {} })),
      axios.get('/api/gateway/events').catch(() => ({ data: {} })),
      axios.get('/api/gateway/forward').catch(() => ({ data: {} })),
      axios.get('/api/gateway/temperature').catch(() => ({ data: {} })),
    ])
    const d = gwRes.data || {}
    gw.version = d.version || ''
    gw.serial = d.serial || ''
    gw.spec = d.spec || ''
    gw.duty = d.duty || {}
    gw.rf = d.rf || {}
    gw.temperature = tempRes.data?.temperature ?? null
    ledState.value = !!ledRes.data?.ledState
    forwardingState.value = !!fwdRes.data?.forwarding
    const ev = evtRes.data || {}
    events.log = ev.eventLogging ?? ev.log ?? ev.event_logging ?? true
    events.device = ev.eventDevice ?? ev.device ?? ev.event_device ?? true
    events.sensor = ev.eventSensor ?? ev.sensor ?? ev.event_sensor ?? false
    events.sender = ev.eventSender ?? ev.sender ?? ev.event_sender ?? false
    events.duty = ev.eventDuty ?? ev.duty ?? ev.event_duty ?? true
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load gateway data', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function setLED(val) {
  try { await axios.post('/api/gateway/led', { ledState: val }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Failed to set LED', icon: 'error' }) }
}

async function setEvents() {
  try { await axios.post('/api/gateway/events', events) }
  catch (e) { $q.notify({ color: 'negative', message: 'Failed to set events', icon: 'error' }) }
}

async function setForwarding(val) {
  try { await axios.post('/api/gateway/forward', { state: val }); $q.notify({ color: 'positive', message: 'Forwarding updated', icon: 'check' }) }
  catch (e) { $q.notify({ color: 'negative', message: 'Failed', icon: 'error' }) }
}

async function ping() {
  pinging.value = true; pingResult.value = null
  try { const { data } = await axios.get('/api/gateway/ping'); pingResult.value = !data.error }
  catch (e) { pingResult.value = false }
  finally { pinging.value = false }
}

async function resetGateway() {
  $q.dialog({ title: 'Reset Gateway', message: 'Reset the gateway? This will not delete devices.', cancel: true })
  .onOk(async () => {
    try { await axios.get('/api/gateway/reset'); $q.notify({ color: 'positive', message: 'Gateway reset', icon: 'check' }); setTimeout(loadGatewayData, 2000) }
    catch (e) { $q.notify({ color: 'negative', message: 'Reset failed', icon: 'error' }) }
  })
}

async function iveoFactory() {
  $q.dialog({ title: 'Factory Reset Iveo', message: 'Reset all Iveo channels? This will delete all learned Iveo devices.', cancel: true, ok: { label: 'Reset', color: 'negative' } })
  .onOk(async () => {
    try { await axios.post('/api/iveo/0/factoryReset'); $q.notify({ color: 'positive', message: 'Iveo factory reset done', icon: 'check' }) }
    catch (e) { $q.notify({ color: 'negative', message: 'Failed', icon: 'error' }) }
  })
}

async function factoryReset() {
  $q.dialog({ title: 'FACTORY RESET GATEWAY', message: 'This will DELETE ALL devices, groups, and settings! Are you absolutely sure?', cancel: true, persistent: true, ok: { label: 'FACTORY RESET', color: 'negative' } })
  .onOk(async () => {
    try { await axios.get('/api/gateway/factoryReset'); $q.notify({ color: 'positive', message: 'Factory reset complete', icon: 'check' }); setTimeout(loadGatewayData, 3000) }
    catch (e) { $q.notify({ color: 'negative', message: 'Failed', icon: 'error' }) }
  })
}

onMounted(loadGatewayData)
</script>
