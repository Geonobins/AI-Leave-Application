import { useEffect, type Key } from 'react';
import { BarChart2 } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchBalances } from '../../features/leaves/leavesSlice';
import LeaveBalanceCard from '../../components/employee/LeaveBalanceCard';
import Spinner from '../../components/common/Spinner';

const LeaveBalancePage = () => {
  const dispatch = useAppDispatch();
  const { balances, loading } = useAppSelector((state) => state.leaves);

  useEffect(() => {
    dispatch(fetchBalances());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <BarChart2 className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Leave Balance</h1>
          <p className="text-gray-600">Track your available leave days</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {balances.map((balance: { id: Key | null | undefined; }) => (
          <LeaveBalanceCard key={balance.id} balance={balance} />
        ))}
      </div>
    </div>
  );
};

export default LeaveBalancePage;