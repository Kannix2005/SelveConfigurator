import { boot } from "quasar/wrappers";
import MockAdapter from "axios-mock-adapter";
import axios from "axios";

const mock = new MockAdapter(axios);
if (window.location.href.indexOf("localhost") >= 0) {
  mock.onGet("gatewayData").reply(200, {
    port: "/dev/ttyUSB0",
    state: "Blabla",
    lastLogEvent: "Dingsbums2",
    version: "12314.154545.22",
    serial: "ffaasdfsdaffas1413414",
    spec: "sdafdfdsafdsafds",
    duty: {
      utilization: 1,
      sendingBlocked: false,
    },
    worker: {
      state: "Running",
    },
    queue: {
      txq: {
        items: 0,
      },
      rxq: {
        items: 0,
      },
    },
    repeaterState: "No repeater installed",
  });

  mock.onGet("devices").reply(() => {
    let value = Math.random();
    let mms = "";
    if (value <= 0.3) {
      mms = "UP_ON";
    } else if (value <= 0.6) {
      mms = "STOPPED_OFF";
    } else if (value <= 1) {
      mms = "DOWN_ON";
    }
    return [
      200,
      [
        {
          id: 1,
          type: "device",
          name: "Dingsbums1",
          info: {
            movementState: mms,
            value: Math.floor(Math.random() * 100),
            targetValue: 40,
            unreachable: Math.random() <= 0.5 ? true : false,
            overload: Math.random() <= 0.5 ? true : false,
            obstructed: Math.random() <= 0.5 ? true : false,
            alarm: Math.random() <= 0.5 ? true : false,
            lostSensor: Math.random() <= 0.5 ? true : false,
            automaticMode: Math.random() <= 0.5 ? true : false,
            gatewayNotLearned: Math.random() <= 0.5 ? true : false,
            windAlarm: Math.random() <= 0.5 ? true : false,
            rainAlarm: Math.random() <= 0.5 ? true : false,
            freezingAlarm: Math.random() <= 0.5 ? true : false,
            dayMode: "3",
          },
        },
        { id: 2, type: "sensor", name: "Wohnzimmer", info: [] },
        { id: 3, type: "iveo", name: "Fenster", info: [] },
        {
          id: 4,
          type: "device",
          name: "Schlosswächter Haus",
          info: {
            movementState: mms,
            value: Math.floor(Math.random() * 100),
            targetValue: 60,
            unreachable: false,
            overload: true,
            obstructed: true,
            alarm: true,
            lostSensor: true,
            automaticMode: true,
            gatewayNotLearned: true,
            windAlarm: true,
            rainAlarm: true,
            freezingAlarm: true,
            dayMode: "Day",
          },
        },
        { id: 5, type: "sender", name: "Fenster", info: [] },
        { id: 6, type: "senSim", name: "Handsteuerung", info: [] },
      ],
    ];
  });

  mock.onGet("gateway/events").reply(200, {
    log: Math.random() > 0.5 ? true : false,
    device: Math.random() > 0.5 ? true : false,
    sensor: Math.random() > 0.5 ? true : false,
    sender: Math.random() > 0.5 ? true : false,
    duty: Math.random() > 0.5 ? true : false,
  });

  var ledState = Math.random() > 0.5 ? true : false;

  mock
    .onGet("gateway/led")
    .reply(200, { ledState: Math.random() > 0.5 ? true : false });
  mock.onGet("gateway/reset").reply(200, { result: true });
  mock.onGet("gateway/factoryReset").reply(200, { result: true });
  mock.onGet("gateway/repeater").reply(200, { repeaterState: true });

  mock.onPost("gateway/led").reply(200, function (data) {
    return [200, true];
  });
}
export default boot(async ({ app }) => {
  app.config.globalProperties.$mockApi = mock;
});
