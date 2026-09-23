/** The HTTP contract exposed by the Career Quest backend. Dates are ISO strings. */
export type Grade = "Junior" | "Middle" | "Senior" | "Lead";

export interface Principal {
  role: "employee" | "hr";
  employee_id: string | null;
}

export interface EmployeeSummary {
  employee_id: string;
  full_name: string;
  role: string;
  grade: Grade;
}

export interface Employee extends EmployeeSummary {
  department: string;
  manager_id: string | null;
  hire_date: string;
  tenure_months: number;
  work_format: "office" | "hybrid" | "remote";
  preferred_language: "kk" | "ru" | "en";
  career_goal: { target_role: string; target_grade: Grade } | null;
  skills: Record<string, number>;
  last_review_date: string;
}

export interface History {
  record_id: string;
  employee_id: string;
  event_id: string;
  date: string;
  due_date: string | null;
  status: string;
  completion_pct: number;
  score: number | null;
  feedback_rating: number | null;
  assigned_by: string;
}

export interface Participation {
  source_record_id: string | null;
  event_id: string;
  date: string;
  status: string;
  completed_on: string | null;
  source: History | null;
}

export interface Version {
  revision: number;
  as_of_date: string;
}

export interface EmployeeList extends Version {
  items: EmployeeSummary[];
}

export interface EmployeeDetail extends Version {
  profile: Employee;
  current_skills: Record<string, number>;
  history: Participation[];
}

export interface SkillGap {
  skill_id: string;
  name: string;
  current_level: number;
  required_level: number;
  gap: number;
  is_critical: boolean;
}

export interface TargetAnalysis {
  role: string;
  grade: string;
  gaps: SkillGap[];
  requirement_coverage: number;
}

export interface RecommendationFactor {
  kind: string;
  values: Record<string, string | number | boolean | null>;
  source_ids: string[];
}

export interface Candidate {
  event_id: string;
  title: string;
  possible_skill_gains: Record<string, number>;
  eligibility: { eligible: boolean; reasons: string[]; next_session: string | null };
  factors: RecommendationFactor[];
  score: number | null;
}

export interface Trajectory extends Version {
  employee_id: string;
  next_grade: string | null;
  next_grade_gaps: SkillGap[];
  career_goal_analysis: TargetAnalysis | null;
  requirement_coverage: number | null;
  completed_activities: Participation[];
  candidates: Candidate[];
}

export interface CatalogSkill {
  skill_id: string;
  name: string;
  type: "hard" | "soft";
  category: string;
  description: string;
}

export interface SkillGain {
  skill_id: string;
  gain: number;
  max_level: number;
}

export interface Event {
  event_id: string;
  title: string;
  description: string;
  type: "compliance" | "onboarding" | "course" | "workshop" | "mentoring" | "certification" | "meetup";
  format: "online" | "offline" | "self_paced";
  duration_hours: number;
  mandatory: boolean;
  target_roles: string[];
  target_grades: Grade[];
  develops_skills: SkillGain[];
  prerequisites: Record<string, number>;
  upcoming_sessions: string[];
}

export interface RoleProfile {
  role: string;
  grade: Grade;
  required_skills: Record<string, number>;
  critical_skills: string[];
}

export interface HistoryContext {
  participation: Participation;
  event: Event;
  completion_date_basis: "not_completed" | "historical_date_proxy" | "runtime_recorded";
  included_in_skill_projection: boolean;
}

export interface RoleRequirementContext {
  purpose: "current_role" | "next_grade_benchmark" | "explicit_career_goal";
  profile: RoleProfile;
  analysis: TargetAnalysis;
}

export interface UnknownPreference {
  key: string;
  reason: string;
  suggested_question: string;
}

export interface ExcludedEvent {
  event_id: string;
  reasons: string[];
}

export interface RecommendationContext extends Version {
  employee_id: string;
  current_grade: string;
  employee: Employee;
  current_skills: Record<string, number>;
  skill_catalog: CatalogSkill[];
  proficiency_scale: Record<string, string>;
  history: HistoryContext[];
  event_catalog: Event[];
  role_requirements: RoleRequirementContext[];
  targets: TargetAnalysis[];
  candidates: Candidate[];
  excluded_events: ExcludedEvent[];
  facts: RecommendationFactor[];
  unknown_preferences: UnknownPreference[];
}

export type AIRefinementInput = RecommendationContext;

export interface RecommendationItem {
  event_id: string;
  explanation: string;
  evidence: RecommendationFactor[];
}

export interface RecommendationHypothesis {
  statement: string;
  evidence: RecommendationFactor[];
  needs_confirmation: true;
}

export interface RecommendationResult extends Version {
  status: "success" | "no_candidates";
  employee_id: string;
  recommendations: RecommendationItem[];
  hypotheses: RecommendationHypothesis[];
  clarifying_questions: string[];
}

export interface CompletionCommand {
  command_id: string;
  source_record_id: string | null;
  session_date: string | null;
}

export interface SkillChange {
  skill_id: string;
  before: number;
  after: number;
  gain: number;
}

export interface CompletionResult extends Version {
  command_id: string;
  employee_id: string;
  event_id: string;
  skill_changes: SkillChange[];
  trajectory: Trajectory;
}

export interface ImportResult extends Version {
  added_employees: number;
  unchanged_employees: number;
  added_history: number;
  unchanged_history: number;
}

export interface HRDashboard extends Version {
  skill_gap_counts: { skill_id: string; name: string; employee_count: number }[];
  participation_by_event: { event_id: string; title: string; status_counts: Record<string, number> }[];
  employees_without_candidate: string[];
  recommendation_status: "not_implemented";
  employees_without_recommendation: null;
}

export interface MarketReward {
  id: string;
  title: string;
  description: string;
  price: number;
  category: string;
  art: "cup" | "book" | "bag" | "ticket";
  color: "mint" | "lilac" | "yellow" | "peach";
}

export interface RedeemCommand {
  command_id: string;
  reward_id: string;
}

export interface Redemption extends RedeemCommand {
  employee_id: string;
  price: number;
  balance: number;
  redeemed_on: string;
}

export interface MarketState extends Version {
  rewards: MarketReward[];
  employee_id: string | null;
  balance: number | null;
  earned: number | null;
  spent: number | null;
  coins_per_completion: number;
  redemptions: Redemption[];
}
