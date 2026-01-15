'use client'

import { useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import {
  CheckCircle,
  X,
  AlertTriangle,
  Shield,
  FileText,
} from 'lucide-react'

interface InvoiceLine {
  line_id: string
  description: string
  amount: number
  confidence: number
  source_clause_id: string
  explain: string
}

interface Invoice {
  invoice_id: string
  lines: InvoiceLine[]
  total: number
  aggregate_confidence: number
}

interface ApprovalModalProps {
  isOpen: boolean
  onClose: () => void
  onApprove: (data: any) => void
  invoice: Invoice
}

export function ApprovalModal({
  isOpen,
  onClose,
  onApprove,
  invoice,
}: ApprovalModalProps) {
  const [reviewedLines, setReviewedLines] = useState<Set<string>>(new Set())
  const [approverName, setApproverName] = useState('')
  const [approverEmail, setApproverEmail] = useState('')
  const [approvalNote, setApprovalNote] = useState('')
  const [confirmReviewed, setConfirmReviewed] = useState(false)
  const [error, setError] = useState('')

  const allLinesReviewed = invoice.lines.every((line) =>
    reviewedLines.has(line.line_id)
  )

  const handleToggleLine = (lineId: string) => {
    const newSet = new Set(reviewedLines)
    if (newSet.has(lineId)) {
      newSet.delete(lineId)
    } else {
      newSet.add(lineId)
    }
    setReviewedLines(newSet)
  }

  const handleSubmit = () => {
    setError('')

    if (!approverName.trim()) {
      setError('Please enter your name')
      return
    }

    if (!approverEmail.trim() || !approverEmail.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    if (!allLinesReviewed) {
      setError('Please confirm you have reviewed all line items')
      return
    }

    if (!confirmReviewed) {
      setError('Please check the confirmation box')
      return
    }

    onApprove({
      approver_name: approverName,
      approver_email: approverEmail,
      approval_note: approvalNote,
      confirm_reviewed: true,
    })
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white shadow-xl transition-all">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center">
                    <Shield className="w-6 h-6 text-green-600 mr-3" />
                    <Dialog.Title className="text-lg font-medium text-gray-900">
                      Approve Invoice
                    </Dialog.Title>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 rounded-lg hover:bg-gray-100"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Content */}
                <div className="px-6 py-4 max-h-[60vh] overflow-y-auto">
                  {/* Trust notice */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex">
                      <Shield className="h-5 w-5 text-blue-400 flex-shrink-0" />
                      <div className="ml-3">
                        <p className="text-sm text-blue-700">
                          <strong>Your approval is the final control.</strong> This
                          invoice will not be posted to your ERP until you approve it.
                          Your identity and timestamp will be recorded as audit evidence.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Invoice summary */}
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Invoice Summary
                    </h4>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">
                          {invoice.invoice_id}
                        </span>
                        <span className="text-lg font-bold text-gray-900">
                          ${invoice.total.toLocaleString()}
                        </span>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500">
                        <span>
                          {invoice.lines.length} line items •{' '}
                          {Math.round(invoice.aggregate_confidence * 100)}%
                          confidence
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Line item review */}
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Review Line Items
                    </h4>
                    <p className="text-xs text-gray-500 mb-3">
                      Check each line to confirm you have reviewed it
                    </p>
                    <div className="space-y-2">
                      {invoice.lines.map((line) => (
                        <label
                          key={line.line_id}
                          className={`flex items-start p-3 rounded-lg border cursor-pointer transition-colors ${
                            reviewedLines.has(line.line_id)
                              ? 'border-green-300 bg-green-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={reviewedLines.has(line.line_id)}
                            onChange={() => handleToggleLine(line.line_id)}
                            className="mt-1 h-4 w-4 text-green-600 rounded border-gray-300"
                          />
                          <div className="ml-3 flex-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-gray-900">
                                {line.description}
                              </span>
                              <span className="text-sm font-medium text-gray-900">
                                ${line.amount.toLocaleString()}
                              </span>
                            </div>
                            <div className="mt-1 flex items-center text-xs text-gray-500">
                              <FileText className="w-3 h-3 mr-1" />
                              Clause {line.source_clause_id} •{' '}
                              {Math.round(line.confidence * 100)}% confidence
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Approver info */}
                  <div className="space-y-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Your Name *
                      </label>
                      <input
                        type="text"
                        value={approverName}
                        onChange={(e) => setApproverName(e.target.value)}
                        placeholder="Jane Doe"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Your Email *
                      </label>
                      <input
                        type="email"
                        value={approverEmail}
                        onChange={(e) => setApproverEmail(e.target.value)}
                        placeholder="controller@company.com"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Approval Note (optional)
                      </label>
                      <textarea
                        value={approvalNote}
                        onChange={(e) => setApprovalNote(e.target.value)}
                        placeholder="Reviewed and approved. Ready for posting."
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Final confirmation */}
                  <label className="flex items-start p-4 bg-yellow-50 border border-yellow-200 rounded-lg cursor-pointer">
                    <input
                      type="checkbox"
                      checked={confirmReviewed}
                      onChange={(e) => setConfirmReviewed(e.target.checked)}
                      className="mt-0.5 h-4 w-4 text-yellow-600 rounded border-gray-300"
                    />
                    <span className="ml-3 text-sm text-yellow-800">
                      <strong>I confirm I have reviewed this invoice</strong> and
                      authorize it to be posted to our ERP system. I understand my
                      approval will be recorded as audit evidence.
                    </span>
                  </label>

                  {/* Error message */}
                  {error && (
                    <div className="mt-4 flex items-center text-sm text-red-600">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      {error}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={!allLinesReviewed || !confirmReviewed}
                    className={`flex items-center px-4 py-2 text-sm font-medium text-white rounded-lg ${
                      allLinesReviewed && confirmReviewed
                        ? 'bg-green-600 hover:bg-green-700'
                        : 'bg-gray-300 cursor-not-allowed'
                    }`}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve Invoice
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
