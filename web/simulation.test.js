import test from "node:test";
import assert from "node:assert/strict";
import { DEFAULTS, runPlan } from "./simulation.js";

test("runs a twelve-month plan and uses the supplied seed", () => {
  const plan = Array(12).fill(200);
  const first = runPlan(plan, { seed: 42 });
  const replay = runPlan(plan, { seed: 42 });

  assert.equal(first.months.length, 12);
  assert.deepEqual(first, replay);
  assert.ok(first.months.every((month) => month.hours >= 20 && month.hours <= 30));
});

test("fun spending is neutral at $200 and positive at $400", () => {
  const stableConfig = { ...DEFAULTS, giftChance: 0, badFortuneChance: 0 };
  const neutral = runPlan(Array(12).fill(200), { seed: 9, config: stableConfig });
  const maximum = runPlan(Array(12).fill(400), { seed: 9, config: stableConfig });

  assert.ok(neutral.months.every((month) => month.happinessChange === 0));
  assert.ok(maximum.months.every((month) => month.happinessChange === 200));
  assert.ok(maximum.averageHappiness > neutral.averageHappiness);
});

test("bad fortune never exceeds two events and savings cannot go negative", () => {
  const result = runPlan(Array(12).fill(400), {
    seed: 3,
    config: {
      startingSavings: 0, hourlyWage: 0, giftChance: 0,
      badFortuneChance: 1, maxBadFortunes: 2, badFortuneMoneyLoss: 200,
      badFortuneHappinessLoss: 35, jobLossChance: 1, minHours: 20,
      maxHours: 30, weeksPerMonth: 4.33, rent: 1000, otherExpenses: 400,
      funBaseline: 200, maxFun: 400, noFunHappinessLoss: 20,
      missedRentHappinessLoss: 60, missedOtherExpensesHappinessLoss: 45,
      foodShortageHappinessLoss: 80,
    },
  });

  assert.equal(result.badFortunes, 2);
  assert.ok(result.months.every((month) => month.savings >= 0));
  assert.ok(result.averageHappiness < 0);
});

test("rejects plans that do not have one value per month", () => {
  assert.throws(() => runPlan([200]), /12 monthly/);
  assert.throws(() => runPlan(Array(12).fill(401)), /between \$0 and \$400/);
});
