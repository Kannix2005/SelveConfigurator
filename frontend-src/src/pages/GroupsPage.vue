<template>
  <q-page class="flex-center">
    <div class="q-pa-xl">
      <q-table
        flat
        bordered
        title="Groups"
        :rows="groupData"
        :columns="columns"
        row-key="id"
        :filter="filter"
        :loading="loading"
        :pagination="initialPagination"
      >
        <template v-slot:top>
          <q-btn
            color="primary"
            :disable="loading"
            label="Create Group"
            icon="add"
            @click="createGroupDialog"
          />
          <q-btn
            class="q-ml-sm"
            color="primary"
            label="Refresh"
            icon="refresh"
            @click="loadData"
          />
          <q-space />
          <q-input dense debounce="300" color="primary" v-model="filter">
            <template v-slot:append>
              <q-icon name="search" />
            </template>
          </q-input>
        </template>

        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td v-for="col in props.cols" :key="col.name" :props="props">
              {{ col.value }}
            </q-td>
            <q-td auto-width>
              <div class="q-gutter-sm">
                <!-- Movement Controls -->
                <q-btn
                  size="sm"
                  color="positive"
                  icon="arrow_upward"
                  @click="moveGroup(props.row.id, 'up')"
                >
                  <q-tooltip>Move Up</q-tooltip>
                </q-btn>
                <q-btn
                  size="sm"
                  color="warning"
                  icon="stop"
                  @click="moveGroup(props.row.id, 'stop')"
                >
                  <q-tooltip>Stop</q-tooltip>
                </q-btn>
                <q-btn
                  size="sm"
                  color="negative"
                  icon="arrow_downward"
                  @click="moveGroup(props.row.id, 'down')"
                >
                  <q-tooltip>Move Down</q-tooltip>
                </q-btn>
                
                <!-- Edit/Delete -->
                <q-btn
                  size="sm"
                  color="primary"
                  icon="edit"
                  @click="editGroupDialog(props.row)"
                >
                  <q-tooltip>Edit Group</q-tooltip>
                </q-btn>
                <q-btn
                  size="sm"
                  color="red"
                  icon="delete"
                  @click="deleteGroupDialog(props.row.id, props.row.name)"
                >
                  <q-tooltip>Delete Group</q-tooltip>
                </q-btn>
              </div>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script>
import axios from "axios";
import { defineComponent } from "vue";
import { useQuasar } from "quasar";
import { ref } from "vue";

const columns = [
  {
    name: "id",
    required: true,
    label: "Group ID",
    align: "left",
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: "name",
    required: true,
    label: "Group Name",
    align: "left",
    field: (row) => row.name,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: "device_ids",
    label: "Device IDs",
    align: "left",
    field: (row) => row.device_ids ? row.device_ids.join(', ') : '',
    sortable: false,
  },
];

export default defineComponent({
  name: "GroupsPage",
  setup() {
    let $q = useQuasar();
    return {
      initialPagination: {
        sortBy: "id",
        descending: false,
        page: 1,
        rowsPerPage: 10,
        $q,
      },
    };
  },
  data() {
    return {
      loading: ref(false),
      filter: ref(""),
      columns,
      groupData: [],
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    loadData() {
      this.loading = true;
      axios
        .get("/api/groups")
        .then((val) => {
          console.log("Groups loaded:", val);
          this.groupData = val.data;
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({
            color: 'negative',
            message: 'Error loading groups: ' + err.toString(),
            icon: 'error'
          });
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },

    moveGroup(id, direction) {
      this.loading = true;
      let endpoint = '';
      switch(direction) {
        case 'up':
          endpoint = `/api/groups/${id}/moveUp`;
          break;
        case 'down':
          endpoint = `/api/groups/${id}/moveDown`;
          break;
        case 'stop':
          endpoint = `/api/groups/${id}/stop`;
          break;
      }
      
      axios
        .post(endpoint)
        .then((val) => {
          this.$q.notify({
            color: 'positive',
            message: 'Group command sent successfully',
            icon: 'check'
          });
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({
            color: 'negative',
            message: 'Error: ' + err.toString(),
            icon: 'error'
          });
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },

    createGroupDialog() {
      this.$q.dialog({
        title: 'Create New Group',
        message: 'Enter group details:',
        prompt: {
          model: '',
          type: 'text',
          label: 'Group Name',
        },
        cancel: true,
        persistent: true
      }).onOk(name => {
        // Prompt for device IDs
        this.$q.dialog({
          title: 'Add Devices to Group',
          message: 'Enter device IDs (comma separated):',
          prompt: {
            model: '',
            type: 'text',
            label: 'Device IDs (e.g., 1,2,3)',
          },
          cancel: true,
          persistent: true
        }).onOk(deviceIdsStr => {
          const device_ids = deviceIdsStr.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
          this.createGroup(name, device_ids);
        });
      });
    },

    createGroup(name, device_ids) {
      this.loading = true;
      axios
        .put(`/api/groups/0`, { name, device_ids })
        .then((val) => {
          this.$q.notify({
            color: 'positive',
            message: 'Group created successfully',
            icon: 'check'
          });
          this.loadData();
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({
            color: 'negative',
            message: 'Error creating group: ' + err.toString(),
            icon: 'error'
          });
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },

    editGroupDialog(group) {
      this.$q.dialog({
        title: 'Edit Group',
        message: 'Enter new group name:',
        prompt: {
          model: group.name,
          type: 'text',
          label: 'Group Name',
        },
        cancel: true,
        persistent: true
      }).onOk(name => {
        this.$q.dialog({
          title: 'Edit Device IDs',
          message: 'Enter device IDs (comma separated):',
          prompt: {
            model: group.device_ids ? group.device_ids.join(',') : '',
            type: 'text',
            label: 'Device IDs',
          },
          cancel: true,
          persistent: true
        }).onOk(deviceIdsStr => {
          const device_ids = deviceIdsStr.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
          this.updateGroup(group.id, name, device_ids);
        });
      });
    },

    updateGroup(id, name, device_ids) {
      this.loading = true;
      axios
        .put(`/api/groups/${id}`, { name, device_ids })
        .then((val) => {
          this.$q.notify({
            color: 'positive',
            message: 'Group updated successfully',
            icon: 'check'
          });
          this.loadData();
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({
            color: 'negative',
            message: 'Error updating group: ' + err.toString(),
            icon: 'error'
          });
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },

    deleteGroupDialog(id, name) {
      this.$q.dialog({
        title: 'Confirm',
        message: `Do you really want to delete the group "${name}"?`,
        cancel: true,
        persistent: true,
      }).onOk(() => {
        this.deleteGroup(id);
      });
    },

    deleteGroup(id) {
      this.loading = true;
      axios
        .delete(`/api/groups/${id}`)
        .then((val) => {
          this.$q.notify({
            color: 'positive',
            message: 'Group deleted successfully',
            icon: 'check'
          });
          this.loadData();
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({
            color: 'negative',
            message: 'Error deleting group: ' + err.toString(),
            icon: 'error'
          });
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
  },
});
</script>

<style scoped>
.q-pa-xl {
  width: 100%;
}
</style>
