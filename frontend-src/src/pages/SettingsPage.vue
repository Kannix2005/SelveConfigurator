<template>
  <q-page class="flex flex-center"> Settings </q-page>
</template>

<script>
import { defineComponent } from "vue";
import axios from "axios";

function loadData() {
  axios
    .get("settingsData")
    .then((val) => {
      console.log(val);
      this.gatewayData = val;
    })
    .catch((err) => console.log(err))
    .finally(() => {
      setTimeout(() => {}, 300);
    });
}

export default defineComponent({
  name: "SettingsPage",
  setup() {},
  mounted() {
    loadData();
  },
});
</script>
