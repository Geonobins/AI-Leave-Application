import { useAppSelector } from './store/hooks';
import AppRoutes from './routes/AppRoutes';
import Toast from './components/common/Toast';

function App() {
  const toasts = useAppSelector((state) => state.ui.toasts);

  return (
    <div className="min-h-screen bg-gray-50">
      <AppRoutes />
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map((toast:any) => (
          <Toast key={toast.id} toast={toast} />
        ))}
      </div>
    </div>
  );
}

export default App;