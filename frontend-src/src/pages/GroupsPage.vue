<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h5">Groups</div>
      <q-space />
      <q-btn color="primary" :disable="loading" label="Create Group" icon="add" @click="openCreateDialog" class="q-mr-sm" />
      <q-btn color="primary" label="Refresh" icon="refresh" @click="loadData" />
      <q-input dense debounce="300" color="primary" v-model="filter" class="q-ml-md" placeholder="Search...">
        <template v-slot:append><q-icon name="search" /></template>
      </q-input>
    </div>

    <!-- Create / Edit Dialog -->
    <q-dialog v-model="dialogOpen" persistent>
      <q-card style="min-width: 500px; max-width: 90vw">
        <q-card-section class="row items-center q-pb-none">
          <span class="text-h6">{{ editingGroup ? 'Edit Group' : 'Create Group' }}</span>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model="groupForm.name" label="Group Name" outlined autofocus />
          <div>
            <div class="text-subtitle2 q-mb-sm">Devices</div>
            <div v-if="availableDevices.length === 0" class="text-grey text-caption">No devices loaded.</div>
            <q-option-group
              v-else
              v-model="groupForm.device_ids"
              :options="availableDevices"
              type="checkbox"
              color="primary"
            />
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey" v-close-popup />
          <q-btn flat label="Save" color="positive" :disable="!groupForm.name" @click="saveGroup" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-table
      flat
      bordered
      :rows="groupData"
      :columns="columns"
      row-key="id"
      :filter="filter"
      :loading="loading"
      :pagination="{ sortBy: 'id', rowsPerPage: 10 }"
    >
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">{{ props.row.id }}</q-td>
          <q-td key="name" :props="props">{{ props.row.name }}</q-td>
          <q-td key="device_ids" :props="props">
            {{ props.row.device_ids && props.row.device_ids.length ? props.row.device_ids.join(', ') : '-' }}
          </q-td>
          <q-td key="actions" :props="props">
            <div class="q-gutter-xs">
              <q-btn size="sm" color="positive" icon="arrow_upward" @click="moveGroup(props.row.id, 'up')"><q-tooltip>Move Up</q-tooltip></q-btn>
              <q-btn size="sm" color="warning" icon="stop" @click="moveGroup(props.row.id, 'stop')"><q-tooltip>Stop</q-tooltip></q-btn>
              <q-btn size="sm" color="negative" icon="arrow_downward" @click="moveGroup(props.row.id, 'down')"><q-tooltip>Move Down</q-tooltip></q-btn>
              <q-btn size="sm" color="primary" icon="edit" @click="openEditDialog(props.row)"><q-tooltip>Edit Group</q-tooltip></q-btn>
              <q-btn size="sm" color="red" icon="delete" @click="deleteGroupDialog(props.row.id, props.row.name)"><q-tooltip>Delete Group</q-tooltip></q-btn>
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

const groupData = ref([])
const availableDevices = ref([])
const loading = ref(false)
const filter = ref('')
const dialogOpen = ref(false)
const editingGroup = ref(null)
const groupForm = ref({ name: '', device_ids: [] })

const columns = [
  { name: 'id', label: 'Group ID', field: 'id', sortable: true, align: 'left' },
  { name: 'name', label: 'Group Name', field: 'name', sortable: true, align: 'left' },
  { name: 'device_ids', label: 'Device IDs', field: row => row.device_ids ? row.device_ids.join(', ') : '', align: 'left' },
  { name: 'actions', label: 'Actions', align: 'center' },
]

async function loadDevices() {
  try {
    const { data } = await axios.get('/api/devices')
    availableDevices.value = data.map(d => ({
      label: `${d.id} — ${d.name || 'Unnamed'}`,
      value: d.id,
    }))
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Error loading devices', icon: 'error' })
  }
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/groups')
    groupData.value = data
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Error loading groups', icon: 'error' })
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingGroup.value = null
  groupForm.value = { name: '', device_ids: [] }
  dialogOpen.value = true
}

function openEditDialog(group) {
  editingGroup.value = group
  groupForm.value = {
    name: group.name,
    device_ids: (group.device_ids || []).map(Number),
  }
  dialogOpen.value = true
}

async function saveGroup() {
  if (!groupForm.value.name) return
  try {
    if (editingGroup.value) {
      await axios.put(`/api/groups/${editingGroup.value.id}`, groupForm.value)
      $q.notify({ color: 'positive', message: 'Group updated', icon: 'check' })
    } else {
      await axios.post('/api/groups', groupForm.value)
      $q.notify({ color: 'positive', message: 'Group created', icon: 'check' })
    }
    dialogOpen.value = false
    await loadData()
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Failed to save group', icon: 'error' })
  }
}

async function moveGroup(id, direction) {
  const ep = { up: 'moveUp', down: 'moveDown', stop: 'stop' }[direction]
  try {
    await axios.post(`/api/groups/${id}/${ep}`)
    $q.notify({ color: 'positive', message: 'Command sent', icon: 'check' })
  } catch (e) {
    $q.notify({ color: 'negative', message: 'Command failed', icon: 'error' })
  }
}

function deleteGroupDialog(id, name) {
  $q.dialog({
    title: 'Confirm',
    message: `Delete group "${name}"?`,
    cancel: true,
    persistent: true,
    ok: { label: 'Delete', color: 'negative' },
  }).onOk(async () => {
    try {
      await axios.delete(`/api/groups/${id}`)
      $q.notify({ color: 'positive', message: 'Group deleted', icon: 'check' })
      await loadData()
    } catch (e) {
      $q.notify({ color: 'negative', message: 'Delete failed', icon: 'error' })
    }
  })
}

onMounted(async () => {
  await Promise.all([loadData(), loadDevices()])
})
</script>

<style scoped>
</style>
