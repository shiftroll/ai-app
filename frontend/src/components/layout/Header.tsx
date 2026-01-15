'use client'

import { Bell, User, HelpCircle } from 'lucide-react'

export function Header() {
  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-gray-200">
      <div className="flex items-center">
        <h1 className="text-lg font-semibold text-gray-900">
          Revenue Control Room
        </h1>
        <span className="ml-3 px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
          Phase 1: Supervised
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {/* Help */}
        <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
          <HelpCircle className="w-5 h-5" />
        </button>

        {/* Notifications */}
        <button className="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* User menu */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">Controller</p>
            <p className="text-xs text-gray-500">controller@demo.com</p>
          </div>
          <button className="p-2 text-gray-400 hover:text-gray-600 rounded-full bg-gray-100">
            <User className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
