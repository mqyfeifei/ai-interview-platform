import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";

// 全局样式
import '@/assets/styles/global.scss';
createApp(App).use(store).use(router).mount("#app");
