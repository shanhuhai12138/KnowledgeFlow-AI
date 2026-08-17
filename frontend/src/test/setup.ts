import { createApp, h } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp({ render: () => h('div') })
app.use(ElementPlus)
app.mount('#app')
