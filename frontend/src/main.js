import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'vfonts/Lato.css' // General Font
import 'vfonts/FiraCode.css' // Monospace For code

const app = createApp(App)
app.use(router)
app.mount('#app')
