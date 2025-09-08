import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

function SimpleLogin() {
  return <div>Login Page</div>
}

function SimpleModels() {
  return <div>Models Page</div>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<SimpleLogin />} />
        <Route path="/models" element={<SimpleModels />} />
        <Route path="/" element={<Navigate to="/models" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
