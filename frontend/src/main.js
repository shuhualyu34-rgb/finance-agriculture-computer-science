import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import {
  Button,
  Calendar,
  CellGroup,
  Divider,
  Empty,
  Field,
  Form,
  Icon,
  Image,
  NavBar,
  NoticeBar,
  Picker,
  Popup,
  PullRefresh,
  Step,
  Steps,
  Switch,
  Tab,
  Tabbar,
  TabbarItem,
  Tabs,
  Tag,
  Uploader,
} from 'vant'
import 'vant/lib/index.css'
import './style.css'

const app = createApp(App)

app.use(router)
app.use(Button)
app.use(Calendar)
app.use(CellGroup)
app.use(Divider)
app.use(Empty)
app.use(Field)
app.use(Form)
app.use(Icon)
app.use(Image)
app.use(NavBar)
app.use(NoticeBar)
app.use(Picker)
app.use(Popup)
app.use(PullRefresh)
app.use(Step)
app.use(Steps)
app.use(Switch)
app.use(Tab)
app.use(Tabbar)
app.use(TabbarItem)
app.use(Tabs)
app.use(Tag)
app.use(Uploader)
app.mount('#app')
