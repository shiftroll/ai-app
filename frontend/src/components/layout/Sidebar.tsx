'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FileText,
  Receipt,
  AlertTriangle,
  Clock,
  Settings,
  Home,
  ShieldCheck,
} from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Contract Library', href: '/contracts', icon: FileText },
  { name: 'Invoice Queue', href: '/invoices', icon: Receipt },
  { name: 'Exception Center', href: '/exceptions', icon: AlertTriangle },
  { name: 'Audit Timeline', href: '/audit', icon: Clock },
]

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-gray-200">
        <ShieldCheck className="w-8 h-8 text-primary-600" />
        <span className="ml-2 text-xl font-semibold text-gray-900">
          Crafta
        </span>
      </div>

      {/* Main navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon className={clsx(
                'w-5 h-5 mr-3',
                isActive ? 'text-primary-600' : 'text-gray-400'
              )} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Secondary navigation */}
      <div className="px-4 py-4 border-t border-gray-200">
        {secondaryNavigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-50 hover:text-gray-900"
          >
            <item.icon className="w-5 h-5 mr-3 text-gray-400" />
            {item.name}
          </Link>
        ))}
      </div>

      {/* Trust badge */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            <span className="ml-2 text-xs font-medium text-blue-800">
              Human-in-the-Loop Active
            </span>
          </div>
          <p className="mt-1 text-xs text-blue-600">
            All invoices require manual approval before ERP posting.
          </p>
        </div>
      </div>
    </div>
  )
}
