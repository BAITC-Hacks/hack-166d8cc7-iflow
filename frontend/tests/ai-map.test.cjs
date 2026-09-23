const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const compiled = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/lib/career-data.ts'), 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020},
}).outputText;
const exported = {};
vm.runInNewContext(compiled, {exports: exported, Intl});
const context = {
  event_catalog: [1, 2, 3, 4, 5].map(id => ({event_id: `EV_${id}`, duration_hours: 12, format: 'online'})),
  candidates: [1, 2, 3, 4].map(id => ({event_id: `EV_${id}`})),
};
const recommendation = id => ({event_id: `EV_${id}`, explanation: 'LLM explanation', confidence: 'high', additional_value: null});
test('empty AI selection never fills the map from the catalog', () => {
  assert.equal(exported.planSteps(context, [], 3).length, 0);
});
test('one, two or three recommendations preserve exact AI order, with no filler nodes', () => {
  for (const count of [1, 2, 3]) {
    const items = [3, 1, 2].slice(0, count).map(recommendation);
    const plan = exported.planSteps(context, items, 3);
    assert.equal(JSON.stringify(plan.map(row => row.event.event_id)), JSON.stringify(items.map(row => row.event_id)));
    assert.equal(plan[0].reasons[0], 'LLM explanation');
  }
});
test('pace changes duration only, even for a long live event', () => {
  const slow = exported.planSteps(context, [recommendation(3)], 1);
  const fast = exported.planSteps(context, [recommendation(3)], 5);
  assert.equal(slow[0].event.event_id, fast[0].event.event_id);
  assert.equal(slow[0].end, 12); assert.equal(fast[0].end, 3);
});
test('unknown and no-longer-eligible events do not become map nodes', () => {
  assert.equal(exported.planSteps(context, [recommendation(5), recommendation(99)], 3).length, 0);
});
