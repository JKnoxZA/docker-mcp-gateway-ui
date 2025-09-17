import { formatBytes, API_ENDPOINTS, STATUS, DEFAULT_PAGE_SIZE } from '../utils/constants'

describe('Utils - Constants', () => {
  describe('formatBytes', () => {
    it('formats bytes correctly', () => {
      expect(formatBytes(0)).toBe('0 Bytes')
      expect(formatBytes(1024)).toBe('1 KB')
      expect(formatBytes(1048576)).toBe('1 MB')
      expect(formatBytes(1073741824)).toBe('1 GB')
    })

    it('formats decimal values correctly', () => {
      expect(formatBytes(1536)).toBe('1.5 KB')
      expect(formatBytes(1572864)).toBe('1.5 MB')
    })
  })

  describe('Constants', () => {
    it('has correct API endpoints', () => {
      expect(API_ENDPOINTS.CONTAINERS).toBe('/api/containers')
      expect(API_ENDPOINTS.SERVERS).toBe('/api/mcp/servers')
      expect(API_ENDPOINTS.GATEWAY).toBe('/api/mcp/gateway')
    })

    it('has correct status values', () => {
      expect(STATUS.RUNNING).toBe('running')
      expect(STATUS.STOPPED).toBe('stopped')
      expect(STATUS.ERROR).toBe('error')
    })

    it('has correct default values', () => {
      expect(DEFAULT_PAGE_SIZE).toBe(20)
    })
  })
})