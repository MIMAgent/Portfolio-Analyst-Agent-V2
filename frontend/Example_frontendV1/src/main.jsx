import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="loading-shell">
          <div className="loading-card">
            <h1>Dashboard crashed</h1>
            <p>{this.state.error?.message || String(this.state.error)}</p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

const rootElement = document.getElementById('root')

window.addEventListener('error', (event) => {
  if (!rootElement || rootElement.innerHTML) {
    return
  }
  rootElement.innerHTML = `<div style="padding:32px;font-family:Inter,Arial,sans-serif;"><h1>Runtime error</h1><pre style="white-space:pre-wrap;">${String(event.error?.stack || event.message || event.type)}</pre></div>`
})

window.addEventListener('unhandledrejection', (event) => {
  if (!rootElement || rootElement.innerHTML) {
    return
  }
  rootElement.innerHTML = `<div style="padding:32px;font-family:Inter,Arial,sans-serif;"><h1>Unhandled promise rejection</h1><pre style="white-space:pre-wrap;">${String(event.reason?.stack || event.reason || '')}</pre></div>`
})

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </React.StrictMode>,
)
