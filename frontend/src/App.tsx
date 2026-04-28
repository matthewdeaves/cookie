import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import PullToRefresh from './components/PullToRefresh'

function App() {
  return (
    <>
      <PullToRefresh />
      <RouterProvider router={router} />
    </>
  )
}

export default App
