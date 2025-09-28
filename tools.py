"""
Agent Tools for Traffic Coordination System
This module defines the tools available to agents for coordination tasks.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class TrafficData:
    """Traffic flow data at bottleneck point"""
    timestamp: datetime
    current_flow: int
    capacity_per_minute: int
    queue_length: int
    estimated_wait_time: int

@dataclass
class ClassroomCommitment:
    """Commitment between classroom agents"""
    from_classroom: str
    to_classroom: str
    episode_date: str
    commitment_type: str  # "extend", "shorten", "stagger"
    adjustment_minutes: int
    reciprocal_commitment: Optional[Dict] = None
    status: str = "pending"  # pending, fulfilled, violated
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ClassroomState:
    """Current state of a classroom"""
    classroom_id: str
    current_students: int
    professor_flexibility: float  # -1.0 to 1.0
    base_end_time: str  # "12:30"
    current_adjustment: int = 0  # minutes
    active_commitments: List[ClassroomCommitment] = None
    violation_count: int = 0
    reputation_score: float = 1.0
    
    def __post_init__(self):
        if self.active_commitments is None:
            self.active_commitments = []

class BottleneckTools:
    """Tools available to the Bottleneck Agent"""
    
    @staticmethod
    def analyze_traffic_flow(classroom_states: List[ClassroomState], 
                           capacity_per_minute: int) -> Dict[str, Any]:
        """Analyze current traffic situation and predict congestion"""
        total_students = sum(state.current_students for state in classroom_states)
        base_exit_times = {}
        
        # Group classrooms by their current exit times
        for state in classroom_states:
            exit_time = BottleneckTools.calculate_exit_time(
                state.base_end_time, state.current_adjustment
            )
            if exit_time not in base_exit_times:
                base_exit_times[exit_time] = []
            base_exit_times[exit_time].append({
                'classroom': state.classroom_id,
                'students': state.current_students
            })
        
        # Calculate congestion for each time slot
        congestion_analysis = {}
        max_congestion = 0
        critical_times = []
        
        for time_slot, classrooms in base_exit_times.items():
            slot_students = sum(c['students'] for c in classrooms)
            congestion_ratio = slot_students / capacity_per_minute
            
            congestion_analysis[time_slot] = {
                'students': slot_students,
                'capacity': capacity_per_minute,
                'congestion_ratio': congestion_ratio,
                'classrooms': classrooms,
                'status': 'critical' if congestion_ratio > 1.5 else 
                         'high' if congestion_ratio > 1.0 else
                         'moderate' if congestion_ratio > 0.7 else 'normal'
            }
            
            if congestion_ratio > max_congestion:
                max_congestion = congestion_ratio
            
            if congestion_ratio > 1.0:
                critical_times.append(time_slot)
        
        return {
            'total_students': total_students,
            'capacity_per_minute': capacity_per_minute,
            'max_congestion_ratio': max_congestion,
            'critical_time_slots': critical_times,
            'time_slot_analysis': congestion_analysis,
            'overall_status': 'critical' if max_congestion > 1.5 else
                            'high' if max_congestion > 1.0 else
                            'moderate' if max_congestion > 0.7 else 'normal',
            'recommendations': BottleneckTools._generate_recommendations(
                congestion_analysis, critical_times
            )
        }
    
    @staticmethod
    def _generate_recommendations(congestion_analysis: Dict, 
                                critical_times: List[str]) -> List[Dict]:
        """Generate specific recommendations for traffic management"""
        recommendations = []
        
        for time_slot, analysis in congestion_analysis.items():
            if analysis['status'] in ['critical', 'high']:
                # Find classrooms that could adjust
                flexible_classrooms = []
                rigid_classrooms = []
                
                for classroom_info in analysis['classrooms']:
                    # This would normally check professor flexibility
                    # For now, assume larger classes are more flexible
                    if classroom_info['students'] > 60:
                        flexible_classrooms.append(classroom_info)
                    else:
                        rigid_classrooms.append(classroom_info)
                
                if flexible_classrooms:
                    recommendations.append({
                        'time_slot': time_slot,
                        'priority': 'high' if analysis['status'] == 'critical' else 'medium',
                        'action': 'stagger_exits',
                        'target_classrooms': [c['classroom'] for c in flexible_classrooms],
                        'suggested_adjustments': BottleneckTools._calculate_stagger_adjustments(
                            flexible_classrooms, analysis['capacity']
                        )
                    })
        
        return recommendations
    
    @staticmethod
    def _calculate_stagger_adjustments(classrooms: List[Dict], 
                                     capacity: int) -> List[Dict]:
        """Calculate optimal staggering adjustments"""
        adjustments = []
        total_students = sum(c['students'] for c in classrooms)
        
        if total_students <= capacity:
            return adjustments
        
        # Simple staggering: alternate between early and late adjustments
        for i, classroom in enumerate(classrooms):
            if i % 2 == 0:
                # Even index: suggest earlier exit
                adjustment = -(2 + i // 2)
            else:
                # Odd index: suggest later exit
                adjustment = 2 + i // 2
            
            adjustments.append({
                'classroom': classroom['classroom'],
                'suggested_adjustment': adjustment,
                'rationale': f"Stagger to reduce congestion - {'earlier' if adjustment < 0 else 'later'} exit"
            })
        
        return adjustments
    
    @staticmethod
    def calculate_exit_time(base_time: str, adjustment_minutes: int) -> str:
        """Calculate actual exit time with adjustments"""
        base_dt = datetime.strptime(base_time, "%H:%M")
        adjusted_dt = base_dt + timedelta(minutes=adjustment_minutes)
        return adjusted_dt.strftime("%H:%M")

class ClassroomTools:
    """Tools available to Classroom Agents"""
    
    @staticmethod
    def evaluate_adjustment_feasibility(classroom_state: ClassroomState,
                                      suggested_adjustment: int) -> Dict[str, Any]:
        """Evaluate if a timing adjustment is feasible given professor preferences"""
        flexibility = classroom_state.professor_flexibility
        current_adj = classroom_state.current_adjustment
        total_adjustment = current_adj + suggested_adjustment
        
        # Calculate feasibility score
        if suggested_adjustment > 0:  # Extension
            if flexibility >= 0.3:  # Professor likes longer classes
                feasibility = min(1.0, 0.8 + flexibility * 0.2)
            elif flexibility >= -0.3:  # Neutral professor
                feasibility = 0.6 - abs(suggested_adjustment) * 0.05
            else:  # Professor prefers shorter classes
                feasibility = max(0.1, 0.4 - abs(flexibility) * 0.3)
        else:  # Shortening
            if flexibility <= -0.3:  # Professor likes shorter classes
                feasibility = min(1.0, 0.8 + abs(flexibility) * 0.2)
            elif flexibility >= -0.3 and flexibility <= 0.3:  # Neutral
                feasibility = 0.6 - abs(suggested_adjustment) * 0.05
            else:  # Professor prefers longer classes
                feasibility = max(0.1, 0.4 - flexibility * 0.3)
        
        # Apply constraints
        max_adjustment = 8  # Maximum 8 minutes adjustment
        if abs(total_adjustment) > max_adjustment:
            feasibility *= 0.3
        
        return {
            'feasibility_score': feasibility,
            'is_feasible': feasibility > 0.5,
            'current_total_adjustment': total_adjustment,
            'professor_preference_alignment': ClassroomTools._get_preference_alignment(
                flexibility, suggested_adjustment
            ),
            'constraints': {
                'max_total_adjustment': max_adjustment,
                'within_limits': abs(total_adjustment) <= max_adjustment
            }
        }
    
    @staticmethod
    def _get_preference_alignment(flexibility: float, adjustment: int) -> str:
        """Get description of how adjustment aligns with professor preference"""
        if adjustment > 0:  # Extension
            if flexibility > 0.3:
                return "strongly_aligned"
            elif flexibility > -0.3:
                return "neutral"
            else:
                return "opposed"
        else:  # Shortening
            if flexibility < -0.3:
                return "strongly_aligned"
            elif flexibility < 0.3:
                return "neutral"
            else:
                return "opposed"
    
    @staticmethod
    def create_commitment_offer(from_classroom: ClassroomState,
                              to_classroom_id: str,
                              proposed_adjustment: int,
                              episode_date: str) -> ClassroomCommitment:
        """Create a commitment offer to another classroom"""
        commitment_type = "extend" if proposed_adjustment > 0 else "shorten"
        
        # Create reciprocal commitment for future episode
        future_date = ClassroomTools._get_next_episode_date(episode_date)
        reciprocal = {
            'episode_date': future_date,
            'adjustment_minutes': -proposed_adjustment,  # Opposite adjustment
            'commitment_type': "shorten" if proposed_adjustment > 0 else "extend"
        }
        
        return ClassroomCommitment(
            from_classroom=from_classroom.classroom_id,
            to_classroom=to_classroom_id,
            episode_date=episode_date,
            commitment_type=commitment_type,
            adjustment_minutes=proposed_adjustment,
            reciprocal_commitment=reciprocal
        )
    
    @staticmethod
    def _get_next_episode_date(current_date: str) -> str:
        """Get next episode date (next week)"""
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        next_dt = current_dt + timedelta(days=7)
        return next_dt.strftime("%Y-%m-%d")
    
    @staticmethod
    def evaluate_commitment_offer(classroom_state: ClassroomState,
                                commitment_offer: ClassroomCommitment) -> Dict[str, Any]:
        """Evaluate an incoming commitment offer"""
        # Check current capacity for reciprocal commitment
        can_fulfill_reciprocal = True
        reciprocal_feasibility = 1.0
        
        if commitment_offer.reciprocal_commitment:
            reciprocal_adj = commitment_offer.reciprocal_commitment['adjustment_minutes']
            reciprocal_eval = ClassroomTools.evaluate_adjustment_feasibility(
                classroom_state, reciprocal_adj
            )
            can_fulfill_reciprocal = reciprocal_eval['is_feasible']
            reciprocal_feasibility = reciprocal_eval['feasibility_score']
        
        # Evaluate current adjustment
        current_eval = ClassroomTools.evaluate_adjustment_feasibility(
            classroom_state, commitment_offer.adjustment_minutes
        )
        
        # Calculate overall acceptance score
        current_feasibility = current_eval['feasibility_score']
        
        # Factor in reputation and past commitments
        reputation_bonus = (classroom_state.reputation_score - 0.5) * 0.2
        violation_penalty = classroom_state.violation_count * 0.1
        
        overall_score = (
            current_feasibility * 0.6 + 
            reciprocal_feasibility * 0.4 + 
            reputation_bonus - 
            violation_penalty
        )
        
        return {
            'overall_acceptance_score': overall_score,
            'should_accept': overall_score > 0.6,
            'current_adjustment_feasible': current_eval['is_feasible'],
            'reciprocal_adjustment_feasible': can_fulfill_reciprocal,
            'decision_factors': {
                'current_feasibility': current_feasibility,
                'reciprocal_feasibility': reciprocal_feasibility,
                'reputation_bonus': reputation_bonus,
                'violation_penalty': violation_penalty
            }
        }
    
    @staticmethod
    def update_reputation(classroom_state: ClassroomState, 
                         commitment_fulfilled: bool) -> ClassroomState:
        """Update reputation based on commitment fulfillment"""
        if commitment_fulfilled:
            # Increase reputation, but cap at 1.0
            classroom_state.reputation_score = min(1.0, 
                classroom_state.reputation_score + 0.1)
        else:
            # Decrease reputation and increase violation count
            classroom_state.reputation_score = max(0.0,
                classroom_state.reputation_score - 0.2)
            classroom_state.violation_count += 1
        
        return classroom_state

class CommitmentTracker:
    """System for tracking commitments across episodes"""
    
    def __init__(self):
        self.active_commitments: List[ClassroomCommitment] = []
        self.commitment_history: List[ClassroomCommitment] = []
        self.violation_threshold = 3
    
    def add_commitment(self, commitment: ClassroomCommitment):
        """Add a new commitment to tracking"""
        self.active_commitments.append(commitment)
    
    def get_commitments_for_episode(self, episode_date: str) -> List[ClassroomCommitment]:
        """Get all commitments due for a specific episode"""
        return [c for c in self.active_commitments 
                if c.episode_date == episode_date]
    
    def fulfill_commitment(self, commitment: ClassroomCommitment, 
                          fulfilled: bool) -> Dict[str, Any]:
        """Mark a commitment as fulfilled or violated"""
        commitment.status = "fulfilled" if fulfilled else "violated"
        
        # Move to history
        if commitment in self.active_commitments:
            self.active_commitments.remove(commitment)
        self.commitment_history.append(commitment)
        
        # Check for flagging
        if not fulfilled:
            violations = self.get_violation_count(commitment.to_classroom)
            if violations >= self.violation_threshold:
                return {
                    'flagged': True,
                    'classroom': commitment.to_classroom,
                    'violation_count': violations,
                    'message': f"Classroom {commitment.to_classroom} has been flagged for {violations} violations"
                }
        
        return {'flagged': False}
    
    def get_violation_count(self, classroom_id: str) -> int:
        """Get total violation count for a classroom"""
        return len([c for c in self.commitment_history 
                   if c.to_classroom == classroom_id and c.status == "violated"])
    
    def get_reputation_score(self, classroom_id: str) -> float:
        """Calculate reputation score based on commitment history"""
        classroom_commitments = [c for c in self.commitment_history 
                               if c.to_classroom == classroom_id]
        
        if not classroom_commitments:
            return 1.0  # Perfect score for new participants
        
        fulfilled_count = len([c for c in classroom_commitments if c.status == "fulfilled"])
        total_count = len(classroom_commitments)
        
        base_score = fulfilled_count / total_count
        
        # Apply penalties for violations
        violation_count = total_count - fulfilled_count
        penalty = min(0.5, violation_count * 0.1)
        
        return max(0.0, base_score - penalty)
