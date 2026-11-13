import React from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  label?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  label,
}) => {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <div className="flex flex-col items-center justify-center gap-2 p-4">
      <Loader2 className={cn('animate-spin text-emerald-600', sizeMap[size], className)} />
      {label && <p className="text-xs text-slate-500 font-medium">{label}</p>}
    </div>
  )
}
