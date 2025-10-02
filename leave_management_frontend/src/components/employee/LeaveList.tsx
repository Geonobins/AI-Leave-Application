import { useEffect, type Key } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchLeaves } from '../../features/leaves/leavesSlice';
import LeaveCard from './LeaveCard';
import Spinner from '../common/Spinner';
import { Calendar } from 'lucide-react';

const LeaveList = () => {
  const dispatch = useAppDispatch();
  const { leaves, loading } = useAppSelector((state) => state.leaves);

  useEffect(() => {
    dispatch(fetchLeaves());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  if (leaves.length === 0) {
    return (
      <div className="text-center py-12">
        <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No leave requests yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {leaves.map((leave: { id: Key | null | undefined; }) => (
        <LeaveCard key={leave.id} leave={leave} />
      ))}
    </div>
  );
};

export default LeaveList;