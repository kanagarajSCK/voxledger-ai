import { createBrowserRouter } from 'react-router-dom'
import { RootLayout } from '../layouts/RootLayout'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { CustomerListPage } from '../features/customers/CustomerListPage'
import { CustomerDetailPage } from '../features/customers/CustomerDetailPage'
import { HomePage } from '../features/dashboard/HomePage'
import { NotFoundPage } from '../features/not-found/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'customers',
        element: <CustomerListPage />,
      },
      {
        path: 'customers/:id',
        element: <CustomerDetailPage />,
      },
      {
        path: 'foundation',
        element: <HomePage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
