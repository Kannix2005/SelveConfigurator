<template>
  <q-page class="justify-evenly">
    <div class="row">
      <div class="col-6">
        <q-list bordered class="rounded-borders" padding>
          <q-item-label header>Gateway state</q-item-label>
          <div v-for="(item, key) in gatewayData" v-bind:key="key" class="">
            <q-expansion-item
              :label="labelkeyGateway(key, item)['label']"
              :icon="labelkeyGateway(key, item)['icon']"
              :header-class="labelkeyGateway(key, item)['headerclass']"
              :disable="labelkeyGateway(key, item)['disable']"
              :caption="labelkeyGateway(key, item)['caption']"
              :hidden="labelkeyGateway(key, item)['hidden']"
            ></q-expansion-item>
          </div>
        </q-list>
      </div>

      <div class="col-6">
        <q-list bordered padding>
          <q-item-label header>Gateway functions</q-item-label>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Enable gateway LEDs</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                color="blue"
                v-model="valueLED"
                val="battery"
                @update:model-value="this.setGatewayLED(valueLED)"
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Reset gateway</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn
                color="amber"
                label="Reset"
                @click="this.resetGateway()"
              ></q-btn>
                     <q-separator />
                     <q-item-label header>Advanced Gateway Info</q-item-label>
                     <q-item tag="label" v-ripple>
                       <q-item-section>
                         <q-item-label>Duty Cycle Information</q-item-label>
                       </q-item-section>
                       <q-item-section side>
                         <q-btn
                           color="info"
                           label="Show Duty Info"
                           icon="bar_chart"
                           @click="this.showDutyInfo()"
                         ></q-btn>
                       </q-item-section>
                     </q-item>
                     <q-item tag="label" v-ripple>
                       <q-item-section>
                         <q-item-label>RF Signal Quality</q-item-label>
                       </q-item-section>
                       <q-item-section side>
                         <q-btn
                           color="info"
                           label="Show RF Info"
                           icon="signal_cellular_alt"
                           @click="this.showRFInfo()"
                         ></q-btn>
                       </q-item-section>
                     </q-item>
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Set repeater forwarding</q-item-label>
              <div class="text-h10">
                <q-badge
                  color="blue"
                  :label="gatewayData.repeaterState"
                  outline
                  align="middle"
                >
                </q-badge>
              </div>
            </q-item-section>
            <q-item-section side>
              <q-btn
                color="primary"
                label="Set Repeater"
                @click="this.setRepeater()"
              ></q-btn>
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Set gateway events</q-item-label>

              <q-checkbox
                v-model="events.log"
                label="Log"
                @update:model-value="this.setEvents('log', events.log)"
              />
              <q-checkbox
                v-model="events.device"
                label="Device"
                @update:model-value="this.setEvents('device', events.device)"
              />
              <q-checkbox
                v-model="events.sensor"
                label="Sensor"
                @update:model-value="this.setEvents('sensor', events.sensor)"
              />
              <q-checkbox
                v-model="events.sender"
                label="Sender"
                @update:model-value="this.setEvents('sender', events.sender)"
              />
              <q-checkbox
                v-model="events.duty"
                label="Duty Cycle"
                @update:model-value="this.setEvents('duty', events.duty)"
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Factory reset Iveo channel</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn
                color="red"
                label="Factory reset channel"
                @click="this.iveoFactory()"
              ></q-btn>
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Factory reset gateway</q-item-label>

              <div class="text-h10">
                <q-badge
                  color="red"
                  label="Deletes all devices --- DANGER!!!"
                  align="middle"
                >
                </q-badge>
              </div>
            </q-item-section>
            <q-item-section side>
              <q-btn
                color="red"
                label="FACTORY RESET"
                @click="this.factoryResetGateway()"
              ></q-btn>
            </q-item-section>
          </q-item>
        </q-list>
      </div>
    </div>
  </q-page>
</template>

<script>
import { defineComponent } from "vue";
import axios from "axios";
import { useQuasar } from "quasar";
import { ref } from "vue";

export default defineComponent({
  name: "GatewayPage",
  setup() {
    let $q = useQuasar();
    return { $q };
  },
  data() {
    return {
      gatewayData: [],
      loading: ref(false),
      valueLED: ref(true),
      valueA: ref(true),
      events: {
        log: true,
        device: true,
        sensor: false,
        sender: false,
        duty: true,
      },
    };
  },
  methods: {
    loadGatewayData() {
      this.loading = true;

      axios
        .get("/api/gatewayData")
        .then((val) => {
          this.gatewayData = val.data;
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
      this.getEvents();
      this.getGatewayLED();
    },

    labelkeyGateway(key, value) {
      switch (key) {
        case "state":
          return {
            label: "State",
            icon: "signal_wifi_4_bar",
            headerclass: "",
            disable: true,
            caption: value.toString(),
          };
        case "lastLogEvent":
          return {
            label: "Last Log Event",
            icon: "timeline",
            headerclass: "",
            disable: true,
            caption: value.toString(),
          };
        case "version":
          return {
            label: "Version",
            icon: "tag",
            headerclass: "",
            disable: true,
            caption: value.toString(),
          };
        case "serial":
          return {
            caption: value.toString(),
            icon: "tag",
            headerclass: "",
            disable: true,
            label: "Serial",
          };
        case "spec":
          return {
            caption: value.toString(),
            icon: "tag",
            headerclass: "",
            disable: true,
            label: "Spec",
          };
        case "duty":
          return {
            caption:
              "Utilization: " +
              value.utilization +
              " Sending blocked: " +
              value.sendingBlocked,
            icon: value.sendingBlocked ? "report_problem" : "check",
            headerclass: value.sendingBlocked ? "text-red" : "text-green",
            disable: true,
            label: "Duty",
          };
        case "worker":
          return {
            caption: value.state.toString(),
            icon: "check",
            headerclass: value.state === "Running" ? "text-green" : "text-red",
            disable: true,
            label: "Worker state",
          };
        case "port":
          return {
            caption: value.toString(),
            icon: "power",
            headerclass: "",
            disable: true,
            label: "Port",
          };
        case "queue":
          return {
            caption:
              "Transmitting " +
              value.txq.items +
              " items, Recieved " +
              value.rxq.items +
              " items",
            icon: "pan_tool",
            headerclass: "",
            disable: true,
            label: "Queue state",
          };

        default:
          return {
            caption: value.toString(),
            icon: "question_mark",
            headerclass: "",
            disable: true,
            label: key,
          };
      }
    },

    resetGateway() {
      this.loading = true;
      axios
        .get("/api/gateway/reset")
        .then((val) => {
          this.loadGatewayData();
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    factoryResetGateway() {
      this.loading = true;
      axios
        .get("/api/gateway/factoryReset")
        .then((val) => {
          this.loadGatewayData();
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    iveoFactory() {
      this.loading = true;
      //show popup with security check and selection
    },
    setGatewayLED(val) {
      this.loading = true;
      axios
        .post("/api/gateway/led", { ledState: val })
        .then((val) => {
          this.getGatewayLED();
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    getGatewayLED() {
      this.loading = true;
      axios
        .get("/api/gateway/led")
        .then((val) => {
          this.valueLED = val.data.ledState;
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    setEvents(type, val) {
      this.loading = true;
      axios
        .post("/api/gateway/events", { type: type, value: val })
        .then((val) => {
          this.getGatewayLED();
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    getEvents() {
      this.loading = true;
      axios
        .get("/api/gateway/events")
        .then((val) => {
          this.events = val.data;
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    setRepeater(type, val) {
      this.loading = true;
      //show popup
    },
    getRepeater() {
      this.loading = true;
      axios
        .get("/api/gateway/repeater")
        .then((val) => {
          this.repeaterState = val.data.repeaterState;
        })
        .catch((err) => {
          console.log(err);
          this.$notifyError(err.toString());
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 300);
        });
    },
    showDutyInfo() {
      this.loading = true;
      axios
        .get("/api/gateway/duty")
        .then((val) => {
          const duty = val.data;
          let message = '<div style="text-align: left;">';
          message += `<b>Duty Mode:</b> ${duty.dutyMode ?? 'N/A'}<br>`;
          message += `<b>RF Traffic:</b> ${duty.rfTraffic ?? 'N/A'}<br>`;
          for (const [key, value] of Object.entries(duty)) {
            if (key !== 'dutyMode' && key !== 'rfTraffic' && key !== 'name') {
              message += `<b>${key}:</b> ${JSON.stringify(value)}<br>`;
            }
          }
          message += '</div>';
          this.$q.dialog({
            title: 'Duty Cycle Information',
            message: message,
            html: true,
          });
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({ color: 'negative', message: 'Error loading duty info', icon: 'error' });
        })
        .finally(() => {
          this.loading = false;
        });
    },
    showRFInfo() {
      this.loading = true;
      axios
        .get("/api/gateway/rf")
        .then((val) => {
          const rf = val.data;
          let message = '<div style="text-align: left;">';
          message += `<b>Net Address:</b> ${rf.netAddress ?? 'N/A'}<br>`;
          message += `<b>Reset Count:</b> ${rf.resetCount ?? 'N/A'}<br>`;
          message += `<b>RF Base ID:</b> ${rf.rfBaseId ?? 'N/A'}<br>`;
          message += `<b>RF Sensor ID:</b> ${rf.rfSensorId ?? 'N/A'}<br>`;
          message += `<b>RF Iveo ID:</b> ${rf.rfIveoId ?? 'N/A'}<br>`;
          message += '</div>';
          this.$q.dialog({
            title: 'RF Signal Information',
            message: message,
            html: true,
          });
        })
        .catch((err) => {
          console.log(err);
          this.$q.notify({ color: 'negative', message: 'Error loading RF info', icon: 'error' });
        })
        .finally(() => {
          this.loading = false;
        });
    },
  },
  mounted() {
    this.loadGatewayData();
  },
});
</script>
