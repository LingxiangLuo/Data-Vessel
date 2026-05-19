import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'
import './styles/global.css'
import App from './App.vue'
import router from './router'
import { setupPermissionDirective } from './directives/permission'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ArcoVue)
setupPermissionDirective(app)
app.mount('#app')
