'use client'

import { useState } from 'react'
import {
  AlertTriangle,
  MessageSquare,
  RefreshCw,
  CheckCircle,
  ChevronRight,
  Filter,
} from 'lucide-react'
import Link from 'next/link'

// Sample exception data
const exceptions = [
  {
    id: 'exc_001',
    invoiceId: 'inv_20260117_002',
    lineId: 'l3',
    type: 'low_confidence',
    description: 'Milestone payment - Phase 2 Completion',
    amount: 15000,
    confidence: 0.72,
    reason: 'Confidence 72% below threshold 80%',
    contractClause: 'c3',
    status: 'pending',
    createdAt: '2026-01-17T10:00:00Z',
    assignedTo: null,
    comments: [],
  },
  {
    id: 'exc_002',
    invoiceId: 'inv_20260116_003',
    lineId: 'l5',
    type: 'cfo_required',
    description: 'Revenue recognition - Multi-element arrangement',
    amount: 45000,
    confidence: 0.89,
    reason: 'Rev-rec sensitive item requires CFO approval',
    contractClause: 'c7',
    status: 'pending',
    createdAt: '2026-01-16T14:30:00Z',
    assignedTo: 'cfo@example.com',
    comments: [
      {
        id: 'cmt_001',
        author: 'controller@example.com',
        text: 'Flagged for CFO review due to multi-element arrangement.',
        createdAt: '2026-01-16T15:00:00Z',
      },
    ],
  },
  {
    id: 'exc_003',
    invoiceId: 'inv_20260115_004',
    lineId: 'l2',
    type: 'manual_review',
    description: 'Rate discrepancy - Consulting hours',
    amount: 2400,
    confidence: 0.65,
    reason: 'Extracted rate ($240/hr) differs from expected ($200/hr)',
    contractClause: 'c1',
    status: 'resolved',
    createdAt: '2026-01-15T09:00:00Z',
    resolvedAt: '2026-01-15T11:30:00Z',
    resolvedBy: 'controller@example.com',
    resolution: 'Rate confirmed as $240/hr per amendment dated 2025-11-01',
    comments: [],
  },
]

const typeConfig = {
  low_confidence: { label: 'Low Confidence', color: 'red' },
  cfo_required: { label: 'CFO Required', color: 'yellow' },
  manual_review: { label: 'Manual Review', color: 'orange' },
  missing_data: { label: 'Missing Data', color: 'gray' },
}

export default function ExceptionsPage() {
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'resolved'>('all')

  const filteredExceptions = exceptions.filter((exc) =>
    statusFilter === 'all' ? true : exc.status === statusFilter
  )

  const pendingCount = exceptions.filter((e) => e.status === 'pending').length

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Exception Center</h2>
        <p className="mt-1 text-sm text-gray-500">
          Invoice lines flagged for manual review or clarification.
        </p>
      </div>

      {/* Alert banner */}
      {pendingCount > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-yellow-400 flex-shrink-0" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                {pendingCount} exception{pendingCount > 1 ? 's' : ''} require your attention
              </h3>
              <p className="mt-1 text-sm text-yellow-600">
                These items need review before the invoices can be approved.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-sm">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-gray-500">Status:</span>
        </div>
        <div className="flex space-x-2">
          {(['all', 'pending', 'resolved'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                statusFilter === status
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              {status === 'pending' && pendingCount > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Exception list */}
      <div className="space-y-4">
        {filteredExceptions.map((exception) => {
          const type = typeConfig[exception.type as keyof typeof typeConfig]
          return (
            <div
              key={exception.id}
              className={`bg-white rounded-lg shadow ${
                exception.status === 'resolved' ? 'opacity-75' : ''
              }`}
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <AlertTriangle
                        className={`w-5 h-5 ${
                          exception.status === 'resolved'
                            ? 'text-gray-400'
                            : 'text-yellow-500'
                        }`}
                      />
                      <h3 className="text-sm font-medium text-gray-900">
                        {exception.description}
                      </h3>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${type.color}-100 text-${type.color}-800`}
                      >
                        {type.label}
                      </span>
                      {exception.status === 'resolved' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Resolved
                        </span>
                      )}
                    </div>

                    <div className="mt-2 text-sm text-gray-500">
                      <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                        {exception.invoiceId}
                      </span>
                      <span className="mx-2">•</span>
                      Line {exception.lineId}
                      <span className="mx-2">•</span>
                      Clause {exception.contractClause}
                    </div>

                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-700">
                        <strong>Reason:</strong> {exception.reason}
                      </p>
                    </div>

                    {/* Comments */}
                    {exception.comments.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {exception.comments.map((comment) => (
                          <div
                            key={comment.id}
                            className="flex items-start space-x-2 text-sm"
                          >
                            <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5" />
                            <div>
                              <span className="font-medium text-gray-700">
                                {comment.author}:
                              </span>{' '}
                              <span className="text-gray-600">{comment.text}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Resolution */}
                    {exception.status === 'resolved' && exception.resolution && (
                      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-sm text-green-700">
                          <strong>Resolution:</strong> {exception.resolution}
                        </p>
                        <p className="mt-1 text-xs text-green-600">
                          Resolved by {exception.resolvedBy} on{' '}
                          {new Date(exception.resolvedAt!).toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="ml-6 text-right">
                    <p className="text-lg font-semibold text-gray-900">
                      ${exception.amount.toLocaleString()}
                    </p>
                    <p
                      className={`text-sm ${
                        exception.confidence < 0.8
                          ? 'text-red-600'
                          : 'text-gray-500'
                      }`}
                    >
                      {Math.round(exception.confidence * 100)}% confidence
                    </p>
                  </div>
                </div>

                {/* Actions */}
                {exception.status === 'pending' && (
                  <div className="mt-4 flex items-center justify-end space-x-3">
                    <button className="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                      <MessageSquare className="w-4 h-4 mr-1.5" />
                      Add Comment
                    </button>
                    <button className="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                      <RefreshCw className="w-4 h-4 mr-1.5" />
                      Re-parse
                    </button>
                    <Link
                      href={`/invoices/${exception.invoiceId}`}
                      className="flex items-center px-3 py-1.5 text-sm font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100"
                    >
                      View Invoice
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {filteredExceptions.length === 0 && (
        <div className="text-center py-12">
          <CheckCircle className="mx-auto h-12 w-12 text-green-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No exceptions</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter === 'pending'
              ? 'All exceptions have been resolved.'
              : 'No exceptions match your filter.'}
          </p>
        </div>
      )}
    </div>
  )
}
