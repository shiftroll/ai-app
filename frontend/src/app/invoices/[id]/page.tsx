'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Send,
  FileText,
  AlertTriangle,
  Info,
  Download,
  Edit,
} from 'lucide-react'
import Link from 'next/link'
import { ApprovalModal } from '@/components/invoices/ApprovalModal'

// Sample invoice detail data
const sampleInvoice = {
  invoice_id: 'inv_20260118_001',
  contract_id: 'ctr_20260115_001',
  drafted_by: 'agent_v0.1',
  lines: [
    {
      line_id: 'l1',
      description: 'Consulting hours Dec (10h @ $200)',
      quantity: 10,
      unit: 'hour',
      unit_price: 200,
      amount: 2000,
      source_clause_id: 'c1',
      source_event_ids: ['we_001'],
      explain: 'Derived from timesheet event we_001',
      agent_reasoning:
        'The contract clause c1 specifies a rate of $200/hour for consulting services. Work event we_001 records 10 hours of consulting on 2025-12-12. Multiplying 10 hours by $200/hour yields $2,000. This aligns with the pre-calculated amount in the work event.',
      confidence: 0.93,
      is_exception: false,
      requires_cfo_approval: false,
    },
    {
      line_id: 'l2',
      description: 'Additional consulting hours (5h @ $200)',
      quantity: 5,
      unit: 'hour',
      unit_price: 200,
      amount: 1000,
      source_clause_id: 'c1',
      source_event_ids: ['we_002'],
      explain: 'Derived from timesheet event we_002',
      agent_reasoning:
        'The contract clause c1 specifies a rate of $200/hour. Work event we_002 records 5 hours of additional consulting. Calculation: 5 hours × $200/hour = $1,000.',
      confidence: 0.91,
      is_exception: false,
      requires_cfo_approval: false,
    },
    {
      line_id: 'l3',
      description: 'Milestone: Phase 1 Completion',
      quantity: 1,
      unit: 'fixed',
      unit_price: 12000,
      amount: 12000,
      source_clause_id: 'c2',
      source_event_ids: ['we_003'],
      explain: 'Milestone payment triggered by completion event we_003',
      agent_reasoning:
        'Contract clause c2 specifies a milestone payment of $12,000 upon completion of Phase 1. Work event we_003 indicates Phase 1 acceptance was completed. Manual verification of acceptance is recommended.',
      confidence: 0.88,
      is_exception: false,
      requires_cfo_approval: false,
    },
  ],
  subtotal: 15000,
  tax: 0,
  total: 15000,
  status: 'draft',
  invoice_date: '2026-01-18',
  due_date: '2026-02-17',
  explainability:
    'Invoice derived from contract ctr_20260115_001 with 3 line(s). Used clauses: c1, c2. Linked work events: we_001, we_002, we_003. Aggregate confidence: 91%.',
  aggregate_confidence: 0.91,
  created_at: '2026-01-18T07:00:00Z',
}

export default function InvoiceDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [invoice, setInvoice] = useState(sampleInvoice)

  const handleApprove = async (approvalData: any) => {
    console.log('Approving invoice:', approvalData)
    // TODO: Call API to approve
    setInvoice({ ...invoice, status: 'approved' })
    setShowApprovalModal(false)
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9)
      return 'bg-green-100 text-green-800 border-green-200'
    if (confidence >= 0.8)
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Invoice Draft</h2>
            <p className="text-sm text-gray-500">{invoice.invoice_id}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {invoice.status === 'draft' && (
            <>
              <button className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </button>
              <button
                onClick={() => setShowApprovalModal(true)}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Approve
              </button>
            </>
          )}
          {invoice.status === 'approved' && (
            <button className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
              <Send className="w-4 h-4 mr-2" />
              Push to ERP
            </button>
          )}
          <button className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </button>
        </div>
      </div>

      {/* Status banner */}
      {invoice.status === 'draft' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <Info className="h-5 w-5 text-blue-400 flex-shrink-0" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                This invoice requires your approval
              </h3>
              <p className="mt-1 text-sm text-blue-600">
                Review the line items and explainability below. Click "Approve" when ready
                to proceed. You must confirm you have reviewed each line.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Invoice summary */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Invoice Summary</h3>
        </div>
        <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <dt className="text-sm font-medium text-gray-500">Contract</dt>
            <dd className="mt-1 text-sm text-gray-900">
              <Link
                href={`/contracts/${invoice.contract_id}`}
                className="text-primary-600 hover:underline"
              >
                {invoice.contract_id}
              </Link>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Invoice Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{invoice.invoice_date}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Due Date</dt>
            <dd className="mt-1 text-sm text-gray-900">{invoice.due_date}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Confidence</dt>
            <dd className="mt-1">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getConfidenceBadge(
                  invoice.aggregate_confidence
                )}`}
              >
                {Math.round(invoice.aggregate_confidence * 100)}%
              </span>
            </dd>
          </div>
        </div>
      </div>

      {/* Explainability */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Explainability Summary</h3>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-700">{invoice.explainability}</p>
        </div>
      </div>

      {/* Line items */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Line Items</h3>
          <p className="text-sm text-gray-500">
            Each line includes source clause and detailed reasoning
          </p>
        </div>
        <div className="divide-y divide-gray-200">
          {invoice.lines.map((line) => (
            <div key={line.line_id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                      {line.line_id}
                    </span>
                    <h4 className="text-sm font-medium text-gray-900">
                      {line.description}
                    </h4>
                    {line.is_exception && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        Exception
                      </span>
                    )}
                  </div>

                  <div className="mt-2 text-sm text-gray-500">
                    {line.quantity} {line.unit} × ${line.unit_price.toLocaleString()}
                  </div>

                  {/* Source info */}
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center text-xs text-gray-500 mb-2">
                      <FileText className="w-3 h-3 mr-1" />
                      Source: Clause {line.source_clause_id} • Events:{' '}
                      {line.source_event_ids.join(', ')}
                    </div>
                    <p className="text-sm text-gray-600">{line.explain}</p>
                  </div>

                  {/* Agent reasoning */}
                  <details className="mt-3">
                    <summary className="text-sm text-primary-600 cursor-pointer hover:text-primary-700">
                      View detailed reasoning
                    </summary>
                    <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm text-gray-700">{line.agent_reasoning}</p>
                    </div>
                  </details>
                </div>

                <div className="ml-6 text-right">
                  <p className="text-lg font-semibold text-gray-900">
                    ${line.amount.toLocaleString()}
                  </p>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-1 ${getConfidenceBadge(
                      line.confidence
                    )}`}
                  >
                    {Math.round(line.confidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Totals */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex justify-end space-x-8">
            <div className="text-right">
              <dt className="text-sm font-medium text-gray-500">Subtotal</dt>
              <dd className="text-lg font-medium text-gray-900">
                ${invoice.subtotal.toLocaleString()}
              </dd>
            </div>
            <div className="text-right">
              <dt className="text-sm font-medium text-gray-500">Tax</dt>
              <dd className="text-lg font-medium text-gray-900">
                ${invoice.tax.toLocaleString()}
              </dd>
            </div>
            <div className="text-right">
              <dt className="text-sm font-medium text-gray-500">Total</dt>
              <dd className="text-2xl font-bold text-gray-900">
                ${invoice.total.toLocaleString()}
              </dd>
            </div>
          </div>
        </div>
      </div>

      {/* Approval Modal */}
      <ApprovalModal
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        onApprove={handleApprove}
        invoice={invoice}
      />
    </div>
  )
}
