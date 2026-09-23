export type Grade = "Junior" | "Middle" | "Senior" | "Lead";
export interface EmployeeSummary { employee_id: string; full_name: string; role: string; grade: Grade }
export interface Employee extends EmployeeSummary {
 department: string; manager_id: string | null; hire_date: string; tenure_months: number;
 work_format: "office" | "hybrid" | "remote"; preferred_language: "kk" | "ru" | "en";
 career_goal: {target_role: string; target_grade: Grade} | null;
 skills: Record<string,number>; last_review_date: string;
}
export interface History { record_id: string; employee_id: string; event_id: string; date: string; due_date: string | null; status: string; completion_pct: number; score: number | null; feedback_rating: number | null; assigned_by: string }
export interface Participation { source_record_id: string | null; event_id: string; date: string; status: string; completed_on: string | null; source: History | null }
export interface Version { revision: number; as_of_date: string }
export interface EmployeeList extends Version { items: EmployeeSummary[] }
export interface EmployeeDetail extends Version { profile: Employee; current_skills: Record<string,number>; history: Participation[] }
export interface SkillGap { skill_id: string; name: string; current_level: number; required_level: number; gap: number; is_critical: boolean }
export interface TargetAnalysis { role: string; grade: Grade; gaps: SkillGap[]; requirement_coverage: number }
export interface RecommendationFactor { kind: string; values: Record<string,string | number | boolean | null>; source_ids: string[] }
export interface Candidate { event_id: string; title: string; possible_skill_gains: Record<string,number>; eligibility: { eligible: boolean; reasons: string[]; next_session: string | null }; factors: RecommendationFactor[]; score: number | null }
export interface Trajectory extends Version { employee_id: string; next_grade: Grade | null; next_grade_gaps: SkillGap[]; career_goal_analysis: TargetAnalysis | null; requirement_coverage: number | null; completed_activities: Participation[]; candidates: Candidate[] }
