from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.leave import Leave
from app.models.user import User
from datetime import datetime, timedelta

class AnalyticsService:
    
    @staticmethod
    def get_leave_trends(db: Session, year: int = None):
        """Get leave trends for analytics"""
        if not year:
            year = datetime.now().year
        
        monthly_data = db.query(
            extract('month', Leave.start_date).label('month'),
            Leave.leave_type,
            func.count(Leave.id).label('count')
        ).filter(
            extract('year', Leave.start_date) == year,
            Leave.status == "APPROVED"
        ).group_by('month', Leave.leave_type).all()
        
        return monthly_data
    
    @staticmethod
    def predict_leave_spikes(db: Session):
        """Predict future leave spikes based on historical data"""
        # Get historical data for past 2 years
        two_years_ago = datetime.now() - timedelta(days=730)
        
        historical = db.query(
            extract('month', Leave.start_date).label('month'),
            func.count(Leave.id).label('count')
        ).filter(
            Leave.start_date >= two_years_ago,
            Leave.status == "APPROVED"
        ).group_by('month').all()
        
        # Simple prediction: average historical count per month
        predictions = {}
        for month, count in historical:
            if month not in predictions:
                predictions[month] = []
            predictions[month].append(count)
        
        forecast = {
            month: sum(counts) / len(counts)
            for month, counts in predictions.items()
        }
        
        return forecast
    
    @staticmethod
    def get_department_utilization(db: Session, department: str = None):
        """Get leave utilization by department"""
        query = db.query(
            User.department,
            func.count(Leave.id).label('total_leaves'),
            func.avg(
                func.julianday(Leave.end_date) - func.julianday(Leave.start_date) + 1
            ).label('avg_duration')
        ).join(Leave, User.id == Leave.employee_id).filter(
            Leave.status == "APPROVED"
        )
        
        if department:
            query = query.filter(User.department == department)
        
        results = query.group_by(User.department).all()
        
        return results