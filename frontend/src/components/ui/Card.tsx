import React from 'react'
import { cn } from '../../lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Card: React.FC<CardProps> = ({ className, ...props }) => (
  <div
    className={cn(
      'rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden transition-all',
      className
    )}
    {...props}
  />
)

export const CardHeader: React.FC<CardProps> = ({ className, ...props }) => (
  <div className={cn('p-5 border-b border-slate-100 flex flex-col space-y-1.5', className)} {...props} />
)

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  ...props
}) => (
  <h3 className={cn('text-base font-semibold text-slate-900 tracking-tight', className)} {...props} />
)

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  ...props
}) => (
  <p className={cn('text-xs text-slate-500', className)} {...props} />
)

export const CardContent: React.FC<CardProps> = ({ className, ...props }) => (
  <div className={cn('p-5', className)} {...props} />
)

export const CardFooter: React.FC<CardProps> = ({ className, ...props }) => (
  <div className={cn('p-5 border-t border-slate-100 bg-slate-50/50 flex items-center', className)} {...props} />
)
