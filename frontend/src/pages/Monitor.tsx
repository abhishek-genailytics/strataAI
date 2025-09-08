import React, { useState, useEffect } from 'react'
import DataTable, { Column } from '@/components/shared/DataTable'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/shared/EmptyState'

// Simple analytics types
type UsageSummary = { 
  requests: number
  input_tokens: number
  output_tokens: number
  cost_usd: number 
}

type ModelBreakdown = {
  id: string
  model: string
  requests: number
  tokens: number
  cost: string
}

type UserBreakdown = {
  id: string
  user: string
  requests: number
  tokens: number
  cost: string
}

type RecentError = {
  id: string
  time: string
  endpoint: string
  status: number
  provider: string
  error: string
}

export default function Monitor() {
  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modelBreakdown, setModelBreakdown] = useState<ModelBreakdown[]>([])
  const [userBreakdown, setUserBreakdown] = useState<UserBreakdown[]>([])
  const [recentErrors, setRecentErrors] = useState<RecentError[]>([])

  useEffect(() => {
    // Simple fetch for summary data
    const fetchSummary = async () => {
      try {
        setLoading(true)
        // For now, just show a placeholder since the backend endpoints might not be ready
        setSummary({
          requests: 1250,
          input_tokens: 45000,
          output_tokens: 32000,
          cost_usd: 12.45
        })
        
        // Mock data for tables
        setModelBreakdown([
          { id: '1', model: 'gpt-4o-mini', requests: 850, tokens: 42000, cost: '$8.20' },
          { id: '2', model: 'claude-3.5-sonnet', requests: 400, tokens: 35000, cost: '$4.25' }
        ])
        
        setUserBreakdown([
          { id: '1', user: 'abhishek@genailytics.com', requests: 1250, tokens: 77000, cost: '$12.45' }
        ])
        
        setRecentErrors([])
      } catch (err) {
        setError('Failed to load analytics data')
        console.error('Analytics error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-6">Monitor</h1>
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-6">Monitor</h1>
        <div className="text-red-500">{error}</div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Monitor</h1>
      
      {/* Filters Section */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <Label htmlFor="from-date">From</Label>
              <Input id="from-date" type="date" />
            </div>
            <div>
              <Label htmlFor="to-date">To</Label>
              <Input id="to-date" type="date" />
            </div>
            <div>
              <Label htmlFor="provider">Provider</Label>
              <Select>
                <SelectTrigger id="provider">
                  <SelectValue placeholder="All Providers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="model">Model</Label>
              <Select>
                <SelectTrigger id="model">
                  <SelectValue placeholder="All Models" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                  <SelectItem value="claude-3.5-sonnet">Claude 3.5 Sonnet</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="user">User</Label>
              <Select>
                <SelectTrigger id="user">
                  <SelectValue placeholder="All Users" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Users</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="metric">Metric</Label>
              <Select defaultValue="requests">
                <SelectTrigger id="metric">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="requests">Requests</SelectItem>
                  <SelectItem value="tokens">Tokens</SelectItem>
                  <SelectItem value="cost">Cost</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-muted-foreground">Requests</div>
            <div className="text-2xl font-bold">{summary?.requests.toLocaleString() || '—'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-muted-foreground">Input Tokens</div>
            <div className="text-2xl font-bold">{summary?.input_tokens.toLocaleString() || '—'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-muted-foreground">Output Tokens</div>
            <div className="text-2xl font-bold">{summary?.output_tokens.toLocaleString() || '—'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-muted-foreground">Cost (USD)</div>
            <div className="text-2xl font-bold">${summary?.cost_usd.toFixed(2) || '—'}</div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Over Time Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Usage over time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <EmptyState
              title="No usage data"
              description="Chart will appear when usage data is available"
            />
          </div>
        </CardContent>
      </Card>

      {/* Breakdown Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Breakdown by Model */}
        <Card>
          <CardHeader>
            <CardTitle>Breakdown by model</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 mb-4">
              <EmptyState
                title="No model data"
                description="Chart will show model usage breakdown"
              />
            </div>
            <DataTable
              data={modelBreakdown}
              columns={[
                { key: 'model', header: 'Model', sortable: true },
                { key: 'requests', header: 'Requests', sortable: true, accessor: (m) => m.requests.toLocaleString() },
                { key: 'tokens', header: 'Tokens', sortable: true, accessor: (m) => m.tokens.toLocaleString() },
                { key: 'cost', header: 'Cost', sortable: true }
              ]}
              loading={loading}
              emptyText="No model data available"
            />
          </CardContent>
        </Card>

        {/* Breakdown by User */}
        <Card>
          <CardHeader>
            <CardTitle>Breakdown by user</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 mb-4">
              <EmptyState
                title="No user data"
                description="Chart will show user usage breakdown"
              />
            </div>
            <DataTable
              data={userBreakdown}
              columns={[
                { key: 'user', header: 'User', sortable: true },
                { key: 'requests', header: 'Requests', sortable: true, accessor: (u) => u.requests.toLocaleString() },
                { key: 'tokens', header: 'Tokens', sortable: true, accessor: (u) => u.tokens.toLocaleString() },
                { key: 'cost', header: 'Cost', sortable: true }
              ]}
              loading={loading}
              emptyText="No user data available"
            />
          </CardContent>
        </Card>
      </div>

      {/* Recent Errors */}
      <Card>
        <CardHeader>
          <CardTitle>Recent errors</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={recentErrors}
            columns={[
              { key: 'time', header: 'Time', sortable: true },
              { key: 'endpoint', header: 'Endpoint', sortable: true },
              { 
                key: 'status', 
                header: 'Status', 
                sortable: true,
                accessor: (e) => (
                  <Badge variant={e.status >= 400 ? 'destructive' : 'secondary'}>
                    {e.status}
                  </Badge>
                )
              },
              { key: 'provider', header: 'Provider', sortable: true },
              { key: 'error', header: 'Error', className: 'max-w-xs truncate' }
            ]}
            loading={loading}
            emptyText="No recent errors"
            className="max-h-80"
          />
        </CardContent>
      </Card>
    </div>
  )
}
