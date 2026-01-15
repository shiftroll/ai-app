'use client'

import { FileText, Receipt, AlertTriangle, CheckCircle, DollarSign, Clock } from 'lucide-react'
import Link from 'next/link'

// Sample dashboard data
const stats = [
  { name: 'Active Contracts', value: '12', icon: FileText, href: '/contracts' },
  { name: 'Pending Invoices', value: '5', icon: Receipt, href: '/invoices' },
  { name: 'Exceptions', value: '2', icon: AlertTriangle, href: '/exceptions', alert: true },
  { name: 'Approved Today', value: '3', icon: CheckCircle, href: '/audit' },
]

const recentActivity = [
  {
    id: 1,
    action: 'Invoice approved',
    entity: 'INV-2026-0118',
    actor: 'Jane Doe (Controller)',
    time: '5 minutes ago',
    type: 'approve',
  },
  {
    id: 2,
    action: 'Contract parsed',
    entity: 'MSA-ACME.pdf',
    actor: 'System',
    time: '1 hour ago',
    type: 'parse',
  },
  {
    id: 3,
    action: 'Invoice generated',
    entity: 'INV-2026-0117',
    actor: 'Agent v0.1',
    time: '2 hours ago',
    type: 'generate',
  },
]

const pendingApprovals = [
  {
    id: 'inv_001',
    contract: 'ACME Services MSA',
    amount: 15000,
    confidence: 0.93,
    lines: 3,
    dueDate: '2026-02-15',
  },
  {
    id: 'inv_002',
    contract: 'BlueCo Consulting',
    amount: 8500,
    confidence: 0.87,
    lines: 5,
    dueDate: '2026-02-20',
  },
]

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your contract-to-invoice workflow. All actions require human approval.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link
            key={stat.name}
            href={stat.href}
            className="relative overflow-hidden bg-white rounded-lg shadow px-5 py-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center">
              <div className={`flex-shrink-0 p-3 rounded-lg ${
                stat.alert ? 'bg-red-100' : 'bg-primary-100'
              }`}>
                <stat.icon className={`w-6 h-6 ${
                  stat.alert ? 'text-red-600' : 'text-primary-600'
                }`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Pending Approvals */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-5 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Pending Approvals</h3>
            <p className="text-sm text-gray-500">Invoices awaiting your review</p>
          </div>
          <div className="divide-y divide-gray-200">
            {pendingApprovals.map((invoice) => (
              <Link
                key={invoice.id}
                href={`/invoices/${invoice.id}`}
                className="block px-5 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{invoice.contract}</p>
                    <p className="text-sm text-gray-500">{invoice.lines} line items</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">
                      ${invoice.amount.toLocaleString()}
                    </p>
                    <div className="flex items-center justify-end mt-1">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        invoice.confidence >= 0.9
                          ? 'bg-green-100 text-green-800'
                          : invoice.confidence >= 0.8
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {Math.round(invoice.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
          <div className="px-5 py-3 bg-gray-50 rounded-b-lg">
            <Link
              href="/invoices"
              className="text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              View all pending invoices →
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-5 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
            <p className="text-sm text-gray-500">Latest actions in the system</p>
          </div>
          <div className="divide-y divide-gray-200">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="px-5 py-4">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 w-2 h-2 rounded-full ${
                    activity.type === 'approve'
                      ? 'bg-green-500'
                      : activity.type === 'parse'
                      ? 'bg-blue-500'
                      : 'bg-yellow-500'
                  }`} />
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {activity.action}
                    </p>
                    <p className="text-sm text-gray-500">
                      {activity.entity} • {activity.actor}
                    </p>
                  </div>
                  <div className="flex items-center text-xs text-gray-400">
                    <Clock className="w-3 h-3 mr-1" />
                    {activity.time}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="px-5 py-3 bg-gray-50 rounded-b-lg">
            <Link
              href="/audit"
              className="text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              View full audit trail →
            </Link>
          </div>
        </div>
      </div>

      {/* Trust notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <CheckCircle className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              This is a supervised invoice automation system
            </h3>
            <p className="mt-1 text-sm text-blue-600">
              Every invoice requires explicit approval from a Controller before posting to your ERP.
              All actions are logged and available in the audit trail for compliance purposes.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
