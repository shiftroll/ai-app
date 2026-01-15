'use client'

import { useState } from 'react'
import {
  Receipt,
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertTriangle,
  Send,
  Eye,
  ChevronRight,
} from 'lucide-react'
import Link from 'next/link'

// Sample invoice data
const invoices = [
  {
    id: 'inv_20260118_001',
    contractId: 'ctr_20260115_001',
    contractName: 'MSA-ACME Services',
    status: 'draft',
    linesCount: 3,
    subtotal: 15000,
    tax: 0,
    total: 15000,
    confidence: 0.93,
    invoiceDate: '2026-01-18',
    dueDate: '2026-02-17',
    hasExceptions: false,
    requiresCfo: false,
  },
  {
    id: 'inv_20260117_002',
    contractId: 'ctr_20260110_002',
    contractName: 'TechCorp Consulting',
    status: 'exception',
    linesCount: 5,
    subtotal: 8500,
    tax: 0,
    total: 8500,
    confidence: 0.72,
    invoiceDate: '2026-01-17',
    dueDate: '2026-02-16',
    hasExceptions: true,
    requiresCfo: false,
  },
  {
    id: 'inv_20260115_003',
    contractId: 'ctr_20260108_003',
    contractName: 'BlueCo Implementation',
    status: 'approved',
    linesCount: 8,
    subtotal: 45000,
    tax: 4500,
    total: 49500,
    confidence: 0.97,
    invoiceDate: '2026-01-15',
    dueDate: '2026-02-14',
    hasExceptions: false,
    requiresCfo: true,
    approvedBy: 'Jane Doe',
    approvedAt: '2026-01-16T09:00:00Z',
  },
  {
    id: 'inv_20260110_004',
    contractId: 'ctr_20260105_004',
    contractName: 'Monthly Retainer - Alpha',
    status: 'pushed',
    linesCount: 2,
    subtotal: 5000,
    tax: 0,
    total: 5000,
    confidence: 0.99,
    invoiceDate: '2026-01-10',
    dueDate: '2026-02-09',
    hasExceptions: false,
    requiresCfo: false,
    erpInvoiceId: 'QB-20260110-001',
  },
]

const statusConfig = {
  draft: { label: 'Draft', color: 'gray', icon: Clock },
  pending_review: { label: 'Pending Review', color: 'yellow', icon: Clock },
  exception: { label: 'Exception', color: 'red', icon: AlertTriangle },
  approved: { label: 'Approved', color: 'green', icon: CheckCircle },
  pushed: { label: 'Pushed to ERP', color: 'blue', icon: Send },
  rejected: { label: 'Rejected', color: 'red', icon: AlertTriangle },
}

export default function InvoicesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const filteredInvoices = invoices.filter((inv) => {
    const matchesSearch =
      inv.contractName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.id.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = !statusFilter || inv.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-green-100 text-green-800'
    if (confidence >= 0.8) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Invoice Draft Queue</h2>
        <p className="mt-1 text-sm text-gray-500">
          Review generated invoice drafts. Approve before pushing to ERP.
        </p>
      </div>

      {/* Trust notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <CheckCircle className="h-5 w-5 text-blue-400 flex-shrink-0" />
          <p className="ml-3 text-sm text-blue-700">
            <strong>Supervised Invoice System:</strong> The Controller must approve each invoice
            before it can be posted to your ERP. All approvals are logged for audit.
          </p>
        </div>
      </div>

      {/* Search and filter */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search invoices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter || ''}
          onChange={(e) => setStatusFilter(e.target.value || null)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="exception">Exception</option>
          <option value="approved">Approved</option>
          <option value="pushed">Pushed</option>
        </select>
      </div>

      {/* Invoice cards */}
      <div className="space-y-4">
        {filteredInvoices.map((invoice) => {
          const status = statusConfig[invoice.status as keyof typeof statusConfig]
          return (
            <Link
              key={invoice.id}
              href={`/invoices/${invoice.id}`}
              className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <Receipt className="h-6 w-6 text-gray-400" />
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          {invoice.contractName}
                        </h3>
                        <p className="text-sm text-gray-500">{invoice.id}</p>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center space-x-6 text-sm">
                      <div>
                        <span className="text-gray-500">Lines:</span>{' '}
                        <span className="font-medium">{invoice.linesCount}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Invoice Date:</span>{' '}
                        <span className="font-medium">{invoice.invoiceDate}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Due:</span>{' '}
                        <span className="font-medium">{invoice.dueDate}</span>
                      </div>
                    </div>

                    {invoice.status === 'pushed' && invoice.erpInvoiceId && (
                      <p className="mt-2 text-sm text-gray-500">
                        ERP Reference: <span className="font-mono">{invoice.erpInvoiceId}</span>
                      </p>
                    )}

                    {invoice.status === 'approved' && invoice.approvedBy && (
                      <p className="mt-2 text-sm text-gray-500">
                        Approved by {invoice.approvedBy} on{' '}
                        {new Date(invoice.approvedAt!).toLocaleDateString()}
                      </p>
                    )}
                  </div>

                  <div className="text-right">
                    <p className="text-2xl font-semibold text-gray-900">
                      ${invoice.total.toLocaleString()}
                    </p>

                    <div className="mt-2 flex items-center justify-end space-x-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(
                          invoice.confidence
                        )}`}
                      >
                        {Math.round(invoice.confidence * 100)}% confidence
                      </span>

                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${status.color}-100 text-${status.color}-800`}
                      >
                        <status.icon className="w-3 h-3 mr-1" />
                        {status.label}
                      </span>
                    </div>

                    {invoice.hasExceptions && (
                      <p className="mt-2 text-xs text-red-600">
                        ⚠ Has exceptions requiring review
                      </p>
                    )}

                    {invoice.requiresCfo && invoice.status !== 'pushed' && (
                      <p className="mt-2 text-xs text-yellow-600">
                        🔒 Requires CFO approval
                      </p>
                    )}
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-end text-sm text-primary-600">
                  <span>View details</span>
                  <ChevronRight className="w-4 h-4 ml-1" />
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      {filteredInvoices.length === 0 && (
        <div className="text-center py-12">
          <Receipt className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No invoices found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  )
}
