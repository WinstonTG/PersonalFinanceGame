import test from "node:test";
import assert from "node:assert/strict";
import { DEFAULTS, funHappiness, runPlan } from "./simulation.js";

test("runs a twelve-month plan against the same shared year", () => {
  const plan = Array(12).fill(200);
  const first = runPlan(plan, 150);
  const replay = runPlan(plan, 150);

  assert.equal(first.months.length, 12);
  assert.deepEqual(first, replay);
  assert.ok(first.months.every((month) => month.hours >= 25 && month.hours <= 35));
});
test("fun happiness follows the diminishing-return curve", () => {
  assert.equal(funHappiness(0), 0);
  assert.ok(Math.abs(funHappiness(100) - 195) < 1);
  assert.ok(Math.abs(funHappiness(200) - 294) < 1);
  assert.ok(funHappiness(400) < 400);
});

test("investing grows after bills and bad fortune is capped", () => {
  const config = {
    ...DEFAULTS, startingSavings: 0, hourlyWage: 0, giftChance: 0,
    badFortuneChance: 1, jobLossChance: 1,
  };
  const result = runPlan(Array(12).fill(400), 500, { config });

  assert.equal(result.badFortunes, 2);
  assert.equal(result.investmentBalance, 0);
  assert.ok(result.months.every((month) => month.savings >= 0));
  assert.ok(result.averageHappiness < 0);
});

test("rejects plans that do not have one value per month", () => {
  assert.throws(() => runPlan([200]), /12 monthly/);
  assert.throws(() => runPlan(Array(12).fill(401)), /between \$0 and \$400/);
  assert.throws(() => runPlan(Array(12).fill(200), 501), /between \$0 and \$500/);
});
