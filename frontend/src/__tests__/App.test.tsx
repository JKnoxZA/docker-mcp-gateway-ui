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

describe('App Component', () => {
  it('exports App component', () => {
    const App = require('../App').default
    expect(App).toBeDefined()
    expect(typeof App).toBe('function')
  })

  it('has correct function name', () => {
    const App = require('../App').default
    expect(App.name).toBe('App')
  })
})