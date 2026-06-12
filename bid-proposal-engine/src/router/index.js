import { createRouter, createWebHistory } from 'vue-router'
import SplashView from '../views/SplashView.vue'
import UploadView from '../views/UploadView.vue'
import DashboardView from '../views/DashboardView.vue'
import ProposalView from '../views/ProposalView.vue'

const routes = [
  {
    path: '/',
    name: 'Splash',
    component: SplashView,
    meta: { title: 'BidEngine' },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: UploadView,
    meta: { title: 'Upload RFP' },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { title: 'Dashboard' },
  },
  {
    path: '/proposal',
    name: 'Proposal',
    component: ProposalView,
    meta: { title: 'AI Proposal' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
