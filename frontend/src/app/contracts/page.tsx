'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Upload,
  FileText,
  Search,
  Filter,
  MoreVertical,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
} from 'lucide-react'
import Link from 'next/link'

// Sample contract data
const contracts = [
  {
    id: 'ctr_20260115_001',
    filename: 'MSA-ACME.pdf',
    uploadedBy: 'ridho@example.com',
    uploadTime: '2026-01-15T10:12:00Z',
    status: 'parsed',
    parties: ['ACME Services', 'BlueCo'],
    termsCount: 5,
    currency: 'USD',
    totalValue: 150000,
  },
  {
    id: 'ctr_20260110_002',
    filename: 'Consulting-Agreement-TechCorp.pdf',
    uploadedBy: 'finance@example.com',
    uploadTime: '2026-01-10T08:30:00Z',
    status: 'parsed',
    parties: ['TechCorp Ltd.', 'Our Company'],
    termsCount: 8,
    currency: 'USD',
    totalValue: 85000,
  },
  {
    id: 'ctr_20260118_003',
    filename: 'SOW-ProjectAlpha.docx',
    uploadedBy: 'pm@example.com',
    uploadTime: '2026-01-18T14:20:00Z',
    status: 'parsing',
    parties: [],
    termsCount: 0,
    currency: 'USD',
    totalValue: null,
  },
]

const statusConfig = {
  parsed: { label: 'Parsed', color: 'green', icon: CheckCircle },
  parsing: { label: 'Parsing...', color: 'yellow', icon: Clock },
  failed: { label: 'Failed', color: 'red', icon: AlertCircle },
  uploaded: { label: 'Uploaded', color: 'gray', icon: FileText },
}

export default function ContractsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true)
    // TODO: Implement actual upload
    console.log('Uploading files:', acceptedFiles)
    setTimeout(() => setIsUploading(false), 2000)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
  })

  const filteredContracts = contracts.filter(
    (c) =>
      c.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.parties.some((p) => p.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Contract Library</h2>
          <p className="mt-1 text-sm text-gray-500">
            Upload and manage contracts. AI extracts billing terms automatically.
          </p>
        </div>
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-4 text-sm font-medium text-gray-900">
          {isDragActive
            ? 'Drop files here...'
            : isUploading
            ? 'Uploading...'
            : 'Drop contract files here, or click to select'}
        </p>
        <p className="mt-1 text-xs text-gray-500">PDF and DOCX files supported</p>
      </div>

      {/* Search and filter */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search contracts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <button className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="w-4 h-4 mr-2" />
          Filter
        </button>
      </div>

      {/* Contracts table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contract
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Parties
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Terms
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Value
              </th>
              <th className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredContracts.map((contract) => {
              const status = statusConfig[contract.status as keyof typeof statusConfig]
              return (
                <tr key={contract.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className="h-8 w-8 text-gray-400" />
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {contract.filename}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(contract.uploadTime).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {contract.parties.join(' ↔ ') || 'Extracting...'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${status.color}-100 text-${status.color}-800`}>
                      <status.icon className="w-3 h-3 mr-1" />
                      {status.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {contract.termsCount > 0 ? (
                      `${contract.termsCount} terms extracted`
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {contract.totalValue ? (
                      `$${contract.totalValue.toLocaleString()}`
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      href={`/contracts/${contract.id}`}
                      className="text-primary-600 hover:text-primary-900 mr-4"
                    >
                      <Eye className="h-5 w-5 inline" />
                    </Link>
                    <button className="text-gray-400 hover:text-gray-600">
                      <MoreVertical className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
