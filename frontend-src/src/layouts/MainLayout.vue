<template>
  <q-layout view="lHh lpR lfr">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title> Selve Configurator </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered :width="200">
      <q-tabs vertical>
        <q-item-label header> Menu </q-item-label>
        <q-route-tab name="Devices" label="Devices" icon="blinds" to="/" exact />
        <q-route-tab
          name="Groups"
          label="Groups"
          icon="group_work"
          to="/groups"
          exact
        />
        <q-route-tab
          name="Sensors"
          label="Sensors"
          icon="sensors"
          to="/sensors"
          exact
        />
        <q-route-tab
          name="Senders"
          label="Senders"
          icon="settings_remote"
          to="/senders"
          exact
        />
        <q-route-tab
          name="Iveo"
          label="Iveo"
          icon="cast"
          to="/iveo"
          exact
        />
        <q-route-tab
          name="SenSim"
          label="SenSim"
          icon="science"
          to="/sensim"
          exact
        />
        <q-separator />
        <q-item-label header> System </q-item-label>
        <q-route-tab
          name="Gateway"
          label="Gateway"
          icon="router"
          to="/gateway"
          exact
        />
        <q-route-tab
          name="Firmware"
          label="Firmware"
          icon="system_update"
          to="/firmware"
          exact
        />
        <q-route-tab
          name="XMLLog"
          label="XML Log"
          icon="code"
          to="/xmllog"
          exact
        />
        <q-route-tab
          name="Settings"
          label="Settings"
          icon="settings"
          to="/settings"
          exact
        />
      </q-tabs>
    </q-drawer>

    <q-page-container>
      <router-view></router-view>
      <q-page-scroller
        position="bottom-right"
        :scroll-offset="150"
        :offset="[18, 18]"
      >
        <q-btn fab icon="keyboard_arrow_up" color="accent" />
      </q-page-scroller>
    </q-page-container>
  </q-layout>
</template>

<script>
import { defineComponent, ref } from "vue";

export default defineComponent({
  name: "MainLayout",

  components: {},

  setup() {
    const leftDrawerOpen = ref(false);

    return {
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
      },
    };
  },
});
</script>
