import type {Trajectory as TrajectoryData} from "@/lib/types";
export function Trajectory({data}:{data:TrajectoryData}) {
 return <section><h2>Career trajectory</h2><p>Next grade: {data.next_grade ?? "Highest grade in this dataset"}</p>
 {data.requirement_coverage!==null && <p>Requirement coverage: {Math.round(data.requirement_coverage*100)}%</p>}
 <table><thead><tr><th>Skill</th><th>Current</th><th>Required</th><th>Gap</th><th>Critical</th></tr></thead><tbody>{data.next_grade_gaps.map(g=><tr key={g.skill_id}><td>{g.name}</td><td>{g.current_level}</td><td>{g.required_level}</td><td>{g.gap}</td><td>{g.is_critical?"Yes":"No"}</td></tr>)}</tbody></table>
 {data.career_goal_analysis && <p>Career goal: {data.career_goal_analysis.role} / {data.career_goal_analysis.grade} — {Math.round(data.career_goal_analysis.requirement_coverage*100)}% requirement coverage</p>}
 <h2>Eligible development activities</h2><p>Deterministic candidates. AI recommendations and ranking are not implemented.</p>
 <div className="cards">{data.candidates.map(c=><article key={c.event_id}><h3>{c.title}</h3><p>{c.eligibility.next_session ? `Next session: ${c.eligibility.next_session}`:"Self-paced"}</p><p>Possible gains: {Object.entries(c.possible_skill_gains).map(([k,v])=>`${k}: +${v}`).join(", ")}</p></article>)}</div>
 {!data.candidates.length && <p>No eligible activity closes the current target gaps.</p>}</section>;
}
