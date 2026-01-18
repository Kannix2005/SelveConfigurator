import { boot } from "quasar/wrappers";
import { Notify } from "quasar";
import { useQuasar } from "quasar";

export default boot(async ({ app }) => {
  const notifyError = (msg) => {
    Notify.create({
      color: "red",
      textColor: "white",
      icon: "error",
      message: msg,
      position: "top",
      avatar: "",
      multiLine: true,
      actions: [
        {
          label: "Dismiss",
          color: "yellow",
          handler: () => {
            /* console.log('wooow') */
          },
        },
      ],

      timeout: 3000,
    });
  };
  app.config.globalProperties.$notifyError = notifyError;
});
