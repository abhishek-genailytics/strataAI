import React, { Component, ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { hasError: boolean; error?: Error }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }
  
  static getDerivedStateFromError(error: Error) { 
    return { hasError: true, error } 
  }
  
  componentDidCatch(error: Error) { 
    console.error(error) 
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6">
          <div className="text-xl font-semibold mb-2">Something went wrong</div>
          <div className="text-sm text-slate-600">{this.state.error?.message ?? 'Unknown error'}</div>
        </div>
      )
    }
    return this.props.children
  }
}
