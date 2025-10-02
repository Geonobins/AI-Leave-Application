from datetime import datetime, timedelta, date
from typing import Dict, List
import json
import requests
from collections import defaultdict, Counter
from app.config import settings

class AnalyticsAIService:
    """AI-powered analytics service for actionable insights"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def analyze_trends(self, data: Dict) -> Dict:
        """Analyze leave patterns and trends"""
        leaves = data["leaves"]
        
        if not leaves:
            return {"message": "Insufficient data for trend analysis"}
        
        # Monthly distribution
        monthly = defaultdict(lambda: {"count": 0, "days": 0})
        for leave in leaves:
            month = leave["start_date"][:7]  # YYYY-MM
            monthly[month]["count"] += 1
            monthly[month]["days"] += leave["duration"]
        
        # Sort by month
        sorted_monthly = sorted(monthly.items())
        
        # Leave type distribution
        type_dist = Counter(l["leave_type"] for l in leaves)
        
        # Day of week patterns
        dow_patterns = defaultdict(int)
        for leave in leaves:
            start = datetime.fromisoformat(leave["start_date"])
            dow_patterns[start.strftime("%A")] += 1
        
        # Department patterns
        dept_patterns = defaultdict(lambda: {"count": 0, "days": 0, "types": Counter()})
        for leave in leaves:
            dept = leave["department"]
            dept_patterns[dept]["count"] += 1
            dept_patterns[dept]["days"] += leave["duration"]
            dept_patterns[dept]["types"][leave["leave_type"]] += 1
        
        # Seasonal patterns
        seasonal = defaultdict(lambda: {"count": 0, "days": 0})
        for leave in leaves:
            month = datetime.fromisoformat(leave["start_date"]).month
            if month in [12, 1, 2]:
                season = "Winter"
            elif month in [3, 4, 5]:
                season = "Spring"
            elif month in [6, 7, 8]:
                season = "Summer"
            else:
                season = "Fall"
            seasonal[season]["count"] += 1
            seasonal[season]["days"] += leave["duration"]
        
        return {
            "monthly_trend": [
                {"month": m, "requests": d["count"], "days": d["days"]}
                for m, d in sorted_monthly
            ],
            "leave_types": dict(type_dist),
            "day_of_week": dict(dow_patterns),
            "departments": {
                dept: {
                    "requests": data["count"],
                    "days": data["days"],
                    "top_type": data["types"].most_common(1)[0][0] if data["types"] else None
                }
                for dept, data in dept_patterns.items()
            },
            "seasonal": dict(seasonal)
        }
    
    def predict_patterns(self, data: Dict) -> Dict:
        """Predict future leave patterns using AI"""
        leaves = data["leaves"]
        balances = data["balances"]
        
        if not leaves:
            return {"message": "Insufficient historical data"}
        
        # Calculate historical patterns
        monthly_avg = defaultdict(list)
        for leave in leaves:
            month = datetime.fromisoformat(leave["start_date"]).month
            monthly_avg[month].append(leave["duration"])
        
        # Average by month
        monthly_predictions = {}
        for month in range(1, 13):
            if month in monthly_avg:
                avg_days = sum(monthly_avg[month]) / len(monthly_avg[month])
                avg_requests = len(monthly_avg[month])
            else:
                avg_days = 0
                avg_requests = 0
            monthly_predictions[month] = {
                "avg_requests": round(avg_requests, 1),
                "avg_days": round(avg_days, 1)
            }
        
        # Predict next 90 days based on historical patterns
        today = date.today()
        next_90_days = []
        
        for i in range(3):  # Next 3 months
            future_month = (today.month + i) % 12
            if future_month == 0:
                future_month = 12
            
            prediction = monthly_predictions.get(future_month, {"avg_requests": 0, "avg_days": 0})
            next_90_days.append({
                "month": datetime(today.year, future_month, 1).strftime("%B"),
                "predicted_requests": prediction["avg_requests"],
                "predicted_days": prediction["avg_days"]
            })
        
        # Predict high-demand periods
        high_demand = []
        for month, pred in monthly_predictions.items():
            if pred["avg_requests"] > 0:
                all_requests = [p["avg_requests"] for p in monthly_predictions.values() if p["avg_requests"] > 0]
                if all_requests:
                    avg_all = sum(all_requests) / len(all_requests)
                    if pred["avg_requests"] > avg_all * 1.3:  # 30% above average
                        high_demand.append({
                            "month": datetime(2000, month, 1).strftime("%B"),
                            "expected_requests": pred["avg_requests"],
                            "above_average": round((pred["avg_requests"] / avg_all - 1) * 100, 1)
                        })
        
        # Predict employees likely to request leave soon
        likely_requests = []
        for balance in balances:
            if balance["available"] > 0:
                # High available balance = likely to take leave
                utilization = balance["utilization"]
                if utilization < 30 and balance["available"] >= 5:
                    likely_requests.append({
                        "employee": balance["employee_name"],
                        "department": balance["department"],
                        "available_days": balance["available"],
                        "likelihood": "HIGH" if utilization < 15 else "MEDIUM",
                        "reason": f"Low utilization ({round(utilization, 1)}%), {balance['available']} days available"
                    })
        
        likely_requests.sort(key=lambda x: x["available_days"], reverse=True)
        
        return {
            "next_90_days": next_90_days,
            "high_demand_periods": high_demand,
            "likely_leave_requests": likely_requests[:10],  # Top 10
            "prediction_confidence": "MEDIUM" if len(leaves) > 20 else "LOW"
        }
    
    def identify_risks(self, data: Dict) -> Dict:
        """Identify operational risks"""
        leaves = data["leaves"]
        users = data["users"]
        balances = data["balances"]
        
        risks = {
            "critical": [],
            "high": [],
            "medium": []
        }
        
        # Risk 1: Department understaffing
        dept_leave_days = defaultdict(int)
        dept_sizes = defaultdict(int)
        
        for user in users:
            dept_sizes[user["department"]] += 1
        
        # Count current and upcoming leaves by department
        today = date.today()
        next_30_days = today + timedelta(days=30)
        
        for leave in leaves:
            if leave["approved"]:
                leave_start = datetime.fromisoformat(leave["start_date"]).date()
                leave_end = datetime.fromisoformat(leave["end_date"]).date()
                
                # Check if leave overlaps with next 30 days
                if leave_start <= next_30_days and leave_end >= today:
                    dept_leave_days[leave["department"]] += leave["duration"]
        
        for dept, total_days in dept_leave_days.items():
            dept_size = dept_sizes.get(dept, 1)
            avg_days_per_person = total_days / dept_size
            
            if avg_days_per_person > 10:  # Critical if avg > 10 days per person
                risks["critical"].append({
                    "type": "UNDERSTAFFING",
                    "department": dept,
                    "severity": "CRITICAL",
                    "description": f"{dept} will have {total_days} leave days in next 30 days",
                    "impact": f"Average {round(avg_days_per_person, 1)} days per employee",
                    "recommendation": "Consider staggering leaves or hiring temporary support"
                })
            elif avg_days_per_person > 5:
                risks["high"].append({
                    "type": "UNDERSTAFFING",
                    "department": dept,
                    "severity": "HIGH",
                    "description": f"{dept} has elevated leave volume upcoming",
                    "impact": f"Average {round(avg_days_per_person, 1)} days per employee"
                })
        
        # Risk 2: Unused leave accumulation (burnout risk)
        for balance in balances:
            if balance["available"] > balance["total"] * 0.7:  # More than 70% unused
                risks["medium"].append({
                    "type": "BURNOUT_RISK",
                    "employee": balance["employee_name"],
                    "department": balance["department"],
                    "severity": "MEDIUM",
                    "description": f"{balance['employee_name']} has {balance['available']} unused days",
                    "impact": "Employee may not be taking adequate rest",
                    "recommendation": "Encourage employee to use leave balance"
                })
        
        # Risk 3: Seasonal clustering
        seasonal_leaves = defaultdict(int)
        for leave in leaves:
            month = datetime.fromisoformat(leave["start_date"]).month
            if month in [12, 1]:  # Year-end period
                seasonal_leaves["year_end"] += 1
            elif month in [6, 7, 8]:  # Summer
                seasonal_leaves["summer"] += 1
        
        total_leaves = len(leaves)
        if total_leaves > 0:
            year_end_pct = (seasonal_leaves["year_end"] / total_leaves) * 100
            summer_pct = (seasonal_leaves["summer"] / total_leaves) * 100
            
            if year_end_pct > 40:
                risks["high"].append({
                    "type": "SEASONAL_CLUSTERING",
                    "period": "Year-end",
                    "severity": "HIGH",
                    "description": f"{year_end_pct:.0f}% of leaves concentrated in Dec-Jan",
                    "impact": "Potential operational disruption during holidays",
                    "recommendation": "Implement leave blackout periods or rotation policy"
                })
            
            if summer_pct > 50:
                risks["high"].append({
                    "type": "SEASONAL_CLUSTERING",
                    "period": "Summer",
                    "severity": "HIGH",
                    "description": f"{summer_pct:.0f}% of leaves concentrated in summer",
                    "impact": "Reduced capacity during peak period"
                })
        
        return {
            "critical_risks": risks["critical"],
            "high_risks": risks["high"],
            "medium_risks": risks["medium"],
            "total_risks": len(risks["critical"]) + len(risks["high"]) + len(risks["medium"]),
            "risk_score": len(risks["critical"]) * 10 + len(risks["high"]) * 5 + len(risks["medium"]) * 2
        }
    
    def generate_recommendations(
        self,
        data: Dict,
        trends: Dict,
        risks: Dict
    ) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Based on risks
        critical_count = len(risks.get("critical_risks", []))
        if critical_count > 0:
            recommendations.append({
                "priority": "URGENT",
                "category": "STAFFING",
                "title": "Address Critical Staffing Risks",
                "description": f"{critical_count} critical staffing risk(s) identified",
                "actions": [
                    "Review upcoming leaves in affected departments",
                    "Consider temporary staffing or workload redistribution",
                    "Implement leave approval restrictions for peak periods"
                ],
                "impact": "HIGH"
            })
        
        # Based on leave utilization
        balances = data.get("balances", [])
        low_utilization = [b for b in balances if b["utilization"] < 30]
        
        if len(low_utilization) > len(balances) * 0.3:  # More than 30% underutilizing
            recommendations.append({
                "priority": "HIGH",
                "category": "WELLNESS",
                "title": "Improve Leave Utilization",
                "description": f"{len(low_utilization)} employees using <30% of their leave",
                "actions": [
                    "Send reminders about available leave balances",
                    "Encourage managers to promote work-life balance",
                    "Consider mandatory minimum leave policy",
                    "Investigate workload and culture issues"
                ],
                "impact": "MEDIUM"
            })
        
        # Based on seasonal trends
        seasonal = trends.get("seasonal", {})
        if seasonal:
            max_season = max(seasonal.items(), key=lambda x: x[1]["count"])
            if max_season[1]["count"] > sum(s["count"] for s in seasonal.values()) * 0.4:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "PLANNING",
                    "title": "Address Seasonal Imbalance",
                    "description": f"{max_season[0]} has {max_season[1]['count']} requests (highest concentration)",
                    "actions": [
                        "Introduce incentives for off-peak leave",
                        "Implement rotation schedules for popular periods",
                        "Plan for seasonal capacity needs in advance"
                    ],
                    "impact": "MEDIUM"
                })
        
        # Based on department patterns
        dept_data = trends.get("departments", {})
        if dept_data:
            high_leave_depts = [
                (dept, data) for dept, data in dept_data.items()
                if data["requests"] > 0
            ]
            
            if high_leave_depts:
                high_leave_depts.sort(key=lambda x: x[1]["requests"], reverse=True)
                top_dept = high_leave_depts[0]
                
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "ANALYTICS",
                    "title": f"Monitor {top_dept[0]} Department",
                    "description": f"{top_dept[0]} has highest leave volume ({top_dept[1]['requests']} requests)",
                    "actions": [
                        "Review workload distribution in the department",
                        "Check for burnout indicators",
                        "Ensure adequate backup coverage",
                        "Consider team size and capacity"
                    ],
                    "impact": "MEDIUM"
                })
        
        # Policy recommendations
        leaves = data.get("leaves", [])
        if leaves:
            avg_duration = sum(l["duration"] for l in leaves) / len(leaves)
            if avg_duration < 2:
                recommendations.append({
                    "priority": "LOW",
                    "category": "POLICY",
                    "title": "Review Leave Duration Patterns",
                    "description": f"Average leave duration is {avg_duration:.1f} days (very short)",
                    "actions": [
                        "Investigate if employees feel pressured to take short leaves",
                        "Promote longer rest periods for better recovery",
                        "Review minimum leave duration policies"
                    ],
                    "impact": "LOW"
                })
        
        return recommendations
    
    def generate_insights_summary(
        self,
        summary: Dict,
        trends: Dict,
        predictions: Dict,
        risks: Dict
    ) -> str:
        """Generate natural language insights using AI"""
        
        # Build context for AI
        context = f"""
LEAVE ANALYTICS SUMMARY:
- Total Requests: {summary.get('total_requests', 0)}
- Approval Rate: {summary.get('approval_rate', 0)}%
- Total Days Taken: {summary.get('total_days_taken', 0)}
- Average Duration: {summary.get('avg_duration', 0)} days

KEY TRENDS:
{json.dumps(trends, indent=2, default=str)}

PREDICTIONS:
{json.dumps(predictions, indent=2, default=str)}

RISKS IDENTIFIED:
- Critical: {len(risks.get('critical_risks', []))}
- High: {len(risks.get('high_risks', []))}
- Medium: {len(risks.get('medium_risks', []))}
"""

        system_prompt = """You are an HR analytics expert. Generate a concise, actionable insights summary (3-4 sentences) that:

1. Highlights the most important finding
2. Identifies the biggest risk or opportunity
3. Provides one clear recommendation

Be direct and focus on what matters most for HR decision-making. Avoid generic statements."""

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                },
                timeout=8
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                return ai_response.strip()
                
        except Exception as e:
            print(f"AI insights generation failed: {e}")
        
        # Fallback insights
        insights = []
        
        # Most important metric
        approval_rate = summary.get("approval_rate", 0)
        if approval_rate < 70:
            insights.append(f"Your approval rate of {approval_rate}% is below optimal levels, suggesting potential issues with leave policies or management.")
        elif approval_rate > 95:
            insights.append(f"Excellent approval rate of {approval_rate}% indicates healthy leave culture and clear policies.")
        
        # Risk assessment
        total_risks = risks.get("total_risks", 0)
        critical = len(risks.get("critical_risks", []))
        
        if critical > 0:
            insights.append(f"URGENT: {critical} critical staffing risk(s) require immediate attention to prevent operational disruption.")
        elif total_risks > 5:
            insights.append(f"{total_risks} risks identified across departments - proactive intervention needed.")
        else:
            insights.append("Risk levels are manageable with current staffing.")
        
        # Prediction highlight
        likely_requests = predictions.get("likely_leave_requests", [])
        if likely_requests and len(likely_requests) > 0:
            insights.append(f"{len(likely_requests)} employees likely to request leave soon based on low utilization patterns.")
        
        # Top recommendation
        if critical > 0:
            insights.append("RECOMMENDATION: Review and potentially restrict upcoming leaves in critical departments to maintain coverage.")
        else:
            insights.append("RECOMMENDATION: Focus on encouraging underutilized employees to take adequate rest.")
        
        return " ".join(insights)