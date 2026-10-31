import {accountContext} from './lib/accountContext'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles/index.css'

const loading=document.createElement('p');loading.setAttribute('role','status');loading.textContent='Loading your study workspace…';loading.style.padding='24px';document.getElementById('root')!.append(loading)
void accountContext().catch(()=>null).finally(()=>{
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

})
