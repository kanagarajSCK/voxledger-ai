import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './Button'
import { cn } from '../../lib/utils'

export interface ErrorAlertProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Connection Error',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-red-200 bg-red-50/70 p-4 text-red-900',
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold">{title}</h4>
          <p className="mt-1 text-xs text-red-700 leading-relaxed">{message}</p>
          {onRetry && (
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="border-red-300 text-red-800 hover:bg-red-100/50 bg-white"
              >
                <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                Retry Connection
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
