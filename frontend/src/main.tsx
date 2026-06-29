import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/tokens.css'   // custom properties first
import './index.css'           // Tailwind directives
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)