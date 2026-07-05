import { createApp } from "vue";
import Oruga from "@oruga-ui/oruga-next";

import App from "./App.vue";
import "./styles.css";

createApp(App).use(Oruga).mount("#app");
