// Mock all problematic modules
jest.mock('../services/api', () => ({
  projectAPI: {},
  serverAPI: {},
  clientAPI: {},
  permissionAPI: {},
  secretAPI: {},
  gatewayAPI: {},
  containerAPI: {},
  imageAPI: {},
}))

jest.mock('../hooks/useAPI', () => ({
  useServerCatalog: () => ({ data: [], isLoading: false }),
  useGatewayStatus: () => ({ data: null, isLoading: false }),
}))

import App from '../App'

describe('App Component', () => {
  it('exports App component', () => {
    expect(App).toBeDefined()
    expect(typeof App).toBe('function')
  })

  it('has correct function name', () => {
    expect(App.name).toBe('App')
  })
})