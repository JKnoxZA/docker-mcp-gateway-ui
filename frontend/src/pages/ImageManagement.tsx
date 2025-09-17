import React, { useState, useEffect } from 'react'
import {
  HardDrive,
  Trash2,
  Search,
  Filter,
  RefreshCw,
  Download,
  AlertCircle,
  Clock,
  CheckCircle,
  Archive,
  Layers,
  Database,
  FileImage,
  Tag,
  Calendar,
  Info,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { ImageInfo } from '@/types'
import { dockerAPI } from '@/services/api'
import { Button, Input, Modal } from '@/components/common'

interface ImageWithActions extends ImageInfo {
  isLoading?: boolean
}

const ImageManagement: React.FC = () => {
  const [images, setImages] = useState<ImageWithActions[]>([])
  const [filteredImages, setFilteredImages] = useState<ImageWithActions[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [sizeFilter, setSizeFilter] = useState<string>('all')
  const [selectedImage, setSelectedImage] = useState<ImageWithActions | null>(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showRemoveModal, setShowRemoveModal] = useState(false)
  const [imageToRemove, setImageToRemove] = useState<ImageWithActions | null>(null)

  // Load images
  const loadImages = async () => {
    try {
      setLoading(true)
      const data = await dockerAPI.listImages()
      setImages(data)
    } catch (error) {
      console.error('Failed to load images:', error)
      toast.error('Failed to load Docker images')
    } finally {
      setLoading(false)
    }
  }

  // Filter images based on search and size
  useEffect(() => {
    let filtered = images

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (image) =>
          image.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())) ||
          image.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          image.architecture.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Size filter
    if (sizeFilter !== 'all') {
      const sizeThresholds = {
        small: 100 * 1024 * 1024,    // < 100MB
        medium: 1024 * 1024 * 1024,  // 100MB - 1GB
        large: Infinity              // > 1GB
      }

      filtered = filtered.filter((image) => {
        switch (sizeFilter) {
          case 'small':
            return image.size < sizeThresholds.small
          case 'medium':
            return image.size >= sizeThresholds.small && image.size < sizeThresholds.medium
          case 'large':
            return image.size >= sizeThresholds.medium
          default:
            return true
        }
      })
    }

    setFilteredImages(filtered)
  }, [images, searchQuery, sizeFilter])

  // Remove image
  const handleRemoveImage = async (imageId: string, force = false) => {
    try {
      // Set loading state for this image
      setImages((prev) =>
        prev.map((img) => (img.id === imageId ? { ...img, isLoading: true } : img))
      )

      const result = await dockerAPI.removeImage(imageId, force)
      toast.success(`Image ${result.image_id} removed successfully`)

      // Reload images to get updated list
      await loadImages()
    } catch (error) {
      console.error('Failed to remove image:', error)
      toast.error('Failed to remove image')
    } finally {
      // Clear loading state
      setImages((prev) =>
        prev.map((img) => (img.id === imageId ? { ...img, isLoading: false } : img))
      )
    }
  }

  // Show image details
  const showImageDetails = (image: ImageWithActions) => {
    setSelectedImage(image)
    setShowDetailsModal(true)
  }

  // Show remove confirmation
  const showRemoveConfirmation = (image: ImageWithActions) => {
    setImageToRemove(image)
    setShowRemoveModal(true)
  }

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Format created date
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  // Get image tag display
  const getTagDisplay = (tags: string[]) => {
    if (tags.length === 0) return '<none>'
    if (tags.length === 1) return tags[0]
    return `${tags[0]} (+${tags.length - 1} more)`
  }

  // Get size category
  const getSizeCategory = (size: number) => {
    if (size < 100 * 1024 * 1024) return 'small'
    if (size < 1024 * 1024 * 1024) return 'medium'
    return 'large'
  }

  // Get size category color
  const getSizeCategoryColor = (category: string) => {
    switch (category) {
      case 'small':
        return 'text-green-600 bg-green-100'
      case 'medium':
        return 'text-yellow-600 bg-yellow-100'
      case 'large':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  useEffect(() => {
    loadImages()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Docker Images</h1>
          <p className="text-gray-600">Manage your Docker images and repositories</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            onClick={loadImages}
            disabled={loading}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search images by tag, ID, or architecture..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={sizeFilter}
            onChange={(e) => setSizeFilter(e.target.value)}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="all">All Sizes</option>
            <option value="small">Small (&lt; 100MB)</option>
            <option value="medium">Medium (100MB - 1GB)</option>
            <option value="large">Large (&gt; 1GB)</option>
          </select>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <FileImage className="w-8 h-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Images</p>
              <p className="text-2xl font-semibold text-gray-900">{images.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <Database className="w-8 h-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Size</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatFileSize(images.reduce((acc, img) => acc + img.size, 0))}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <Tag className="w-8 h-8 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Tagged Images</p>
              <p className="text-2xl font-semibold text-gray-900">
                {images.filter(img => img.tags.length > 0 && img.tags[0] !== '<none>:<none>').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <Archive className="w-8 h-8 text-orange-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Untagged</p>
              <p className="text-2xl font-semibold text-gray-900">
                {images.filter(img => img.tags.length === 0 || img.tags[0] === '<none>:<none>').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Image List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Loading images...</span>
        </div>
      ) : filteredImages.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
            <HardDrive className="w-full h-full" />
          </div>
          <h3 className="text-sm font-medium text-gray-900">No images found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {images.length === 0
              ? 'No Docker images are available.'
              : 'No images match your current filters.'}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {filteredImages.map((image) => {
              const sizeCategory = getSizeCategory(image.size)
              const sizeCategoryColor = getSizeCategoryColor(sizeCategory)

              return (
                <li key={image.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1 min-w-0">
                      <div className="flex-shrink-0">
                        <FileImage className="w-10 h-10 text-gray-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {getTagDisplay(image.tags)}
                          </p>
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${sizeCategoryColor}`}
                          >
                            {formatFileSize(image.size)}
                          </span>
                        </div>
                        <div className="mt-1 space-y-1">
                          <p className="text-sm text-gray-500">
                            <span className="font-medium">ID:</span> {image.id}
                          </p>
                          <p className="text-sm text-gray-500">
                            <span className="font-medium">Architecture:</span> {image.architecture} | {image.os}
                          </p>
                          <p className="text-sm text-gray-500">
                            <span className="font-medium">Created:</span> {formatDate(image.created)}
                          </p>
                          {image.tags.length > 1 && (
                            <p className="text-sm text-gray-500">
                              <span className="font-medium">All tags:</span> {image.tags.join(', ')}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => showImageDetails(image)}
                        variant="outline"
                        size="sm"
                        className="flex items-center space-x-1"
                      >
                        <Info className="w-4 h-4" />
                        <span>Details</span>
                      </Button>

                      <Button
                        onClick={() => showRemoveConfirmation(image)}
                        disabled={image.isLoading}
                        variant="outline"
                        size="sm"
                        className="flex items-center space-x-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Remove</span>
                      </Button>

                      {image.isLoading && (
                        <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
                      )}
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {/* Image Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title={`Image Details - ${selectedImage?.tags[0] || selectedImage?.id.slice(0, 12)}`}
        size="lg"
      >
        {selectedImage && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Basic Information</h4>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm text-gray-500">Image ID</dt>
                    <dd className="text-sm font-medium text-gray-900 font-mono">{selectedImage.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Size</dt>
                    <dd className="text-sm font-medium text-gray-900">{formatFileSize(selectedImage.size)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Architecture</dt>
                    <dd className="text-sm font-medium text-gray-900">{selectedImage.architecture}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">OS</dt>
                    <dd className="text-sm font-medium text-gray-900">{selectedImage.os}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">Created</dt>
                    <dd className="text-sm font-medium text-gray-900">{formatDate(selectedImage.created)}</dd>
                  </div>
                </dl>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Tags</h4>
                {selectedImage.tags.length > 0 ? (
                  <div className="space-y-1">
                    {selectedImage.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-2 mb-1"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">No tags</p>
                )}
              </div>
            </div>

            {selectedImage.labels && Object.keys(selectedImage.labels).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Labels</h4>
                <div className="bg-gray-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                  <dl className="space-y-1">
                    {Object.entries(selectedImage.labels).map(([key, value]) => (
                      <div key={key} className="flex">
                        <dt className="text-xs text-gray-500 font-medium min-w-0 flex-1">{key}:</dt>
                        <dd className="text-xs text-gray-900 ml-2 break-all">{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Remove Confirmation Modal */}
      <Modal
        isOpen={showRemoveModal}
        onClose={() => setShowRemoveModal(false)}
        title="Remove Docker Image"
        size="md"
      >
        {imageToRemove && (
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-gray-900">
                  Are you sure you want to remove this image? This action cannot be undone.
                </p>
                <div className="mt-2 text-sm text-gray-600">
                  <p><strong>Image:</strong> {getTagDisplay(imageToRemove.tags)}</p>
                  <p><strong>ID:</strong> {imageToRemove.id}</p>
                  <p><strong>Size:</strong> {formatFileSize(imageToRemove.size)}</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3">
              <Button
                onClick={() => setShowRemoveModal(false)}
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  handleRemoveImage(imageToRemove.id, true)
                  setShowRemoveModal(false)
                  setImageToRemove(null)
                }}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Remove Image
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ImageManagement