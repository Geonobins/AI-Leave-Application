import { Calendar } from 'lucide-react';
import LeaveList from '../../components/employee/LeaveList';

const MyLeavesPage = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <Calendar className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Leaves</h1>
          <p className="text-gray-600">View and manage your leave requests</p>
        </div>
      </div>

      <LeaveList />
    </div>
  );
};

export default MyLeavesPage;