import React from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Home, AlertTriangle } from 'lucide-react'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 mb-4">
        <AlertTriangle className="w-8 h-8" />
      </div>
      <h1 className="text-2xl font-bold text-slate-900">Page Not Found</h1>
      <p className="mt-2 text-sm text-slate-500 max-w-sm">
        The requested page does not exist or has not been implemented in Phase 1.
      </p>
      <div className="mt-6">
        <Link to="/">
          <Button variant="primary">
            <Home className="mr-2 h-4 w-4" />
            Back to Foundation Overview
          </Button>
        </Link>
      </div>
    </div>
  )
}
