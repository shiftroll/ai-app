'use client'

import { useState } from 'react'
import {
  Clock,
  Upload,
  Cpu,
  FileText,
  Edit,
  CheckCircle,
  Send,
  Download,
  Filter,
  Search,
  Eye,
  AlertTriangle,
} from 'lucide-react'

// Sample audit log data
const auditLogs = [
  {
    id: 'log_001',
    kind: 'push',
    entityType: 'invoice',
    entityId: 'inv_20260110_004',
    actorId: 'controller@example.com',
    actorType: 'user',
    timestamp: '2026-01-10T16:30:00Z',
    explainabilityText: 'Invoice pushed to QuickBooks',
    confidence: 0.99,
  },
  {
    id: 'log_002',
    kind: 'approve',
    entityType: 'invoice',
    entityId: 'inv_20260110_004',
    actorId: 'controller@example.com',
    actorType: 'user',
    timestamp: '2026-01-10T16:25:00Z',
    explainabilityText: 'Invoice approved for ERP push',
    confidence: 0.99,
  },
  {
    id: 'log_003',
    kind: 'generate',
    entityType: 'invoice',
    entityId: 'inv_20260110_004',
    actorId: 'agent_v0.1',
    actorType: 'agent',
    timestamp: '2026-01-10T15:00:00Z',
    explainabilityText: 'Invoice generated from contract terms and work events',
    confidence: 0.99,
  },
  {
    id: 'log_004',
    kind: 'upload',
    entityType: 'work_events',
    entityId: 'ctr_20260105_004',
    actorId: 'finance@example.com',
    actorType: 'user',
    timestamp: '2026-01-10T14:45:00Z',
    explainabilityText: 'Uploaded 5 work events from timesheet',
  },
  {
    id: 'log_005',
    kind: 'edit',
    entityType: 'contract',
    entityId: 'ctr_20260115_001',
    actorId: 'ridho@example.com',
    actorType: 'user',
    timestamp: '2026-01-15T11:00:00Z',
    explainabilityText: 'Updated clause c1 rate from $180 to $200',
  },
  {
    id: 'log_006',
    kind: 'parse',
    entityType: 'contract',
    entityId: 'ctr_20260115_001',
    actorId: 'agent_v0.1',
    actorType: 'agent',
    timestamp: '2026-01-15T10:15:00Z',
    explainabilityText: 'Contract parsed, extracted 5 billing clauses',
    confidence: 0.91,
  },
  {
    id: 'log_007',
    kind: 'upload',
    entityType: 'contract',
    entityId: 'ctr_20260115_001',
    actorId: 'ridho@example.com',
    actorType: 'user',
    timestamp: '2026-01-15T10:12:00Z',
    explainabilityText: 'Contract uploaded: MSA-ACME.pdf',
  },
]

const kindConfig: Record<string, { label: string; icon: any; color: string }> = {
  upload: { label: 'Upload', icon: Upload, color: 'blue' },
  parse: { label: 'Parse', icon: Cpu, color: 'purple' },
  generate: { label: 'Generate', icon: FileText, color: 'yellow' },
  edit: { label: 'Edit', icon: Edit, color: 'orange' },
  approve: { label: 'Approve', icon: CheckCircle, color: 'green' },
  reject: { label: 'Reject', icon: AlertTriangle, color: 'red' },
  push: { label: 'Push to ERP', icon: Send, color: 'blue' },
  export: { label: 'Export', icon: Download, color: 'gray' },
  view: { label: 'View', icon: Eye, color: 'gray' },
}

export default function AuditPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [entityTypeFilter, setEntityTypeFilter] = useState<string | null>(null)
  const [kindFilter, setKindFilter] = useState<string | null>(null)

  const filteredLogs = auditLogs.filter((log) => {
    const matchesSearch =
      log.entityId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.actorId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.explainabilityText?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
    const matchesEntityType = !entityTypeFilter || log.entityType === entityTypeFilter
    const matchesKind = !kindFilter || log.kind === kindFilter
    return matchesSearch && matchesEntityType && matchesKind
  })

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Audit Timeline</h2>
          <p className="mt-1 text-sm text-gray-500">
            Complete audit trail of all system actions. Every action is logged
            for compliance.
          </p>
        </div>
        <button className="flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700">
          <Download className="w-4 h-4 mr-2" />
          Export Audit Log
        </button>
      </div>

      {/* Search and filters */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by entity ID, actor, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select
          value={entityTypeFilter || ''}
          onChange={(e) => setEntityTypeFilter(e.target.value || null)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">All Entities</option>
          <option value="contract">Contracts</option>
          <option value="invoice">Invoices</option>
          <option value="work_events">Work Events</option>
          <option value="approval">Approvals</option>
        </select>
        <select
          value={kindFilter || ''}
          onChange={(e) => setKindFilter(e.target.value || null)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">All Actions</option>
          <option value="upload">Upload</option>
          <option value="parse">Parse</option>
          <option value="generate">Generate</option>
          <option value="edit">Edit</option>
          <option value="approve">Approve</option>
          <option value="push">Push</option>
        </select>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Activity Log</h3>
          <p className="text-sm text-gray-500">
            Showing {filteredLogs.length} entries
          </p>
        </div>
        <div className="divide-y divide-gray-100">
          {filteredLogs.map((log, index) => {
            const config = kindConfig[log.kind] || kindConfig.view
            const Icon = config.icon
            return (
              <div key={log.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-start">
                  {/* Timeline line */}
                  <div className="flex flex-col items-center mr-4">
                    <div
                      className={`flex items-center justify-center w-8 h-8 rounded-full bg-${config.color}-100`}
                    >
                      <Icon className={`w-4 h-4 text-${config.color}-600`} />
                    </div>
                    {index < filteredLogs.length - 1 && (
                      <div className="w-0.5 h-full bg-gray-200 mt-2" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${config.color}-100 text-${config.color}-800`}
                        >
                          {config.label}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          {log.entityType}/{log.entityId}
                        </span>
                      </div>
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </div>

                    <p className="mt-1 text-sm text-gray-600">
                      {log.explainabilityText}
                    </p>

                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                      <span>
                        By:{' '}
                        <span
                          className={
                            log.actorType === 'agent'
                              ? 'text-purple-600'
                              : 'text-blue-600'
                          }
                        >
                          {log.actorId}
                        </span>
                      </span>
                      {log.confidence && (
                        <span>
                          Confidence: {Math.round(log.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {filteredLogs.length === 0 && (
        <div className="text-center py-12">
          <Clock className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No audit logs found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}

      {/* Audit integrity notice */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex">
          <CheckCircle className="h-5 w-5 text-gray-400 flex-shrink-0" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-gray-700">
              Audit Log Integrity
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              All audit entries are immutable and cryptographically hashed.
              Export the full audit log as a signed PDF for compliance
              documentation.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
