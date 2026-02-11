<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">XML Communication Log</div>
      <q-space />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadLog" :loading="loading" class="q-mr-sm" />
      <q-toggle v-model="autoRefresh" label="Auto-refresh" color="primary" class="q-mr-sm" />
      <q-btn color="negative" label="Clear Log" icon="delete_sweep" @click="clearLog" flat />
    </div>

    <!-- Info Banner -->
    <q-banner class="bg-blue-1 q-mb-md" rounded>
      <template v-slot:avatar>
        <q-icon name="info" color="primary" />
      </template>
      This log shows all XML-RPC style communication between the Configurator and the 
      Home Assistant Selve integration. Useful for debugging and understanding the protocol.
    </q-banner>

    <!-- Filter -->
    <div class="row q-mb-md q-gutter-sm">
      <q-input dense outlined v-model="filter" placeholder="Filter by method or data..." class="col-grow">
        <template v-slot:prepend>
          <q-icon name="filter_list" />
        </template>
        <template v-slot:append>
          <q-icon v-if="filter" name="close" class="cursor-pointer" @click="filter = ''" />
        </template>
      </q-input>
      <q-select dense outlined v-model="filterCategory" :options="categoryOptions" label="Category" style="min-width: 150px" clearable />
    </div>

    <!-- Log Entries -->
    <q-list bordered separator class="rounded-borders">
      <q-item v-if="!filteredLog.length" class="text-grey text-center">
        <q-item-section>
          <q-item-label>No log entries{{ filter || filterCategory ? ' matching filter' : '' }}. Make some API calls to see them here.</q-item-label>
        </q-item-section>
      </q-item>

      <q-expansion-item
        v-for="(entry, idx) in filteredLog"
        :key="idx"
        :icon="entry.response?.error ? 'error' : 'check_circle'"
        :header-class="entry.response?.error ? 'text-negative' : 'text-positive'"
        :label="entry.method"
        :caption="entry.timestamp"
        dense
      >
        <q-card>
          <q-card-section class="q-pa-sm">
            <div class="row q-gutter-md">
              <div class="col">
                <div class="text-caption text-bold q-mb-xs">Request Data:</div>
                <pre class="xml-code bg-grey-2 q-pa-sm rounded-borders">{{ formatJson(entry.data) }}</pre>
              </div>
              <div class="col">
                <div class="text-caption text-bold q-mb-xs">Response:</div>
                <pre class="xml-code q-pa-sm rounded-borders" :class="entry.response?.error ? 'bg-red-1' : 'bg-green-1'">{{ formatJson(entry.response) }}</pre>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </q-expansion-item>
    </q-list>

    <!-- Stats -->
    <div class="row q-mt-md q-gutter-md text-caption text-grey">
      <span>Total entries: {{ logEntries.length }}</span>
      <span>Shown: {{ filteredLog.length }}</span>
      <span>Errors: {{ logEntries.filter(e => e.response?.error).length }}</span>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

const $q = useQuasar()

const logEntries = ref([])
const loading = ref(false)
const autoRefresh = ref(false)
const filter = ref('')
const filterCategory = ref(null)

const categoryOptions = [
  'service', 'param', 'device', 'group', 'iveo',
  'sensor', 'sender', 'sensim', 'firmware', 'command'
]

let refreshInterval = null

const filteredLog = computed(() => {
  let entries = [...logEntries.value].reverse()
  if (filter.value) {
    const q = filter.value.toLowerCase()
    entries = entries.filter(e =>
      e.method?.toLowerCase().includes(q) ||
      JSON.stringify(e.data)?.toLowerCase().includes(q) ||
      JSON.stringify(e.response)?.toLowerCase().includes(q)
    )
  }
  if (filterCategory.value) {
    entries = entries.filter(e => e.method?.includes(filterCategory.value))
  }
  return entries
})

function formatJson(obj) {
  if (!obj) return 'null'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

async function loadLog() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/xmllog')
    logEntries.value = Array.isArray(data) ? data : []
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to load log', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function clearLog() {
  $q.dialog({
    title: 'Clear Log',
    message: 'Clear all log entries?',
    cancel: true,
  }).onOk(async () => {
    try {
      await axios.post('/api/xmllog/clear')
      logEntries.value = []
      $q.notify({ color: 'positive', message: 'Log cleared', icon: 'check' })
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Failed to clear log', icon: 'error' })
    }
  })
}

watch(autoRefresh, (val) => {
  if (val) {
    refreshInterval = setInterval(loadLog, 3000)
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
})

onMounted(loadLog)
onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.xml-code {
  font-family: 'Courier New', monospace;
  font-size: 0.8em;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}
</style>
