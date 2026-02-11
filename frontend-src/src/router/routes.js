const routes = [
  {
    path: "/",
    component: () => import("layouts/MainLayout.vue"),
    children: [
      { path: "", component: () => import("pages/DevicesPage.vue") },
      { path: "groups", component: () => import("pages/GroupsPage.vue") },
      { path: "sensors", component: () => import("pages/SensorsPage.vue") },
      { path: "senders", component: () => import("pages/SendersPage.vue") },
      { path: "iveo", component: () => import("pages/IveoPage.vue") },
      { path: "sensim", component: () => import("pages/SenSimPage.vue") },
      { path: "gateway", component: () => import("pages/GatewayPage.vue") },
      { path: "firmware", component: () => import("pages/FirmwarePage.vue") },
      { path: "xmllog", component: () => import("pages/XMLLogPage.vue") },
      { path: "settings", component: () => import("pages/SettingsPage.vue") },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: "/:catchAll(.*)*",
    component: () => import("pages/ErrorNotFound.vue"),
  },
];

export default routes;
