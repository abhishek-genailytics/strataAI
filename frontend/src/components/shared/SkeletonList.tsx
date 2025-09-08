import React from 'react'
import { Skeleton } from '@/components/ui/skeleton'

interface SkeletonListProps {
  rows?: number
}

export function SkeletonList({ rows = 5 }: SkeletonListProps) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}
