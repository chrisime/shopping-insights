import { createApp } from "vue";
import Oruga from "@oruga-ui/oruga-next";

import App from "./App.vue";
import { t } from "./utils/copy";
import "@oruga-ui/theme-oruga/style.css";
import "./styles.css";

if (typeof document !== "undefined") document.title = t("app.title");
createApp(App).use(Oruga).mount("#app");
