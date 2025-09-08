import React from 'react'
import ReactDOM from 'react-dom/client'

function TestApp() {
  return <div>React is working!</div>
}

ReactDOM.createRoot(document.getElementById('root')!).render(<TestApp />)
