import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

export default function Login(){
  const { signIn } = useAuth()
  const [email,setEmail] = useState('')
  const [password,setPassword] = useState('')
  const [error,setError] = useState<string|null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent)=>{
    e.preventDefault()
    try {
      await signIn(email,password)
      navigate('/models')
    } catch(err:any) {
      setError(err.message)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <Card className="p-6 w-96">
        <form onSubmit={handleSubmit} className="space-y-4">
          <h1 className="text-xl font-semibold">Sign In</h1>
          <Input placeholder="Email" type="email" value={email} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setEmail(e.target.value)} />
          <Input placeholder="Password" type="password" value={password} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setPassword(e.target.value)} />
          {error && <div className="text-sm text-red-500">{error}</div>}
          <Button type="submit" className="w-full">Sign In</Button>
          <div className="text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link to="/signup" className="text-blue-600 hover:underline">
              Sign up
            </Link>
          </div>
        </form>
      </Card>
    </div>
  )
}
