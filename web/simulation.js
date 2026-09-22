export const MONTHS = 12;

export const DEFAULTS = Object.freeze({
  startingSavings: 3000,
  hourlyWage: 15,
  rent: 1000,
  otherExpenses: 400,
  minHours: 20,
  maxHours: 30,
  weeksPerMonth: 4.33,
  giftAmount: 50,
  giftChance: 0.5,
  badFortuneChance: 0.1,
  maxBadFortunes: 2,
  badFortuneMoneyLoss: 200,
  badFortuneHappinessLoss: 35,
  jobLossChance: 0.5,
  funBaseline: 200,
  maxFun: 400,
  noFunHappinessLoss: 20,
  missedRentHappinessLoss: 60,
  missedOtherExpensesHappinessLoss: 45,
  foodShortageHappinessLoss: 80,
});

export function createSeededRandom(seed = 42) {
  let value = Math.abs(Number(seed) || 42) % 2147483647;
  return () => {
    value = (value * 16807) % 2147483647;
    return (value - 1) / 2147483646;
  };
}

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

export function runPlan(funAllocations, { seed = 42, config = DEFAULTS } = {}) {
  if (!Array.isArray(funAllocations) || funAllocations.length !== MONTHS) {
    throw new Error("Your plan needs 12 monthly fun allocations.");
  }
  if (funAllocations.some((value) => !Number.isFinite(value) || value < 0 || value > config.maxFun)) {
    throw new Error("Each fun allocation must be between $0 and $" + config.maxFun + ".");
  }

  const random = createSeededRandom(seed);
  const randomInt = (min, max) => Math.floor(random() * (max - min + 1)) + min;
  let savings = config.startingSavings;
  let happiness = 0;
  let badFortunes = 0;
  let jobLostNextMonth = false;
  const months = [];

  for (let month = 1; month <= MONTHS; month += 1) {
    const hours = randomInt(config.minHours, config.maxHours);
    const jobLost = jobLostNextMonth;
    const income = jobLost ? 0 : config.hourlyWage * hours * config.weeksPerMonth;
    jobLostNextMonth = false;
    savings += income;

    const gift = random() < config.giftChance ? config.giftAmount : 0;
    savings += gift;

    let event = null;
    if (badFortunes < config.maxBadFortunes && random() < config.badFortuneChance) {
      badFortunes += 1;
      savings = Math.max(0, savings - config.badFortuneMoneyLoss);
      event = "Bad fortune";
      if (!jobLost && random() < config.jobLossChance) {
        jobLostNextMonth = true;
        event = "Job loss next month";
      }
    }

    const rentPaid = Math.min(savings, config.rent);
    savings -= rentPaid;
    const otherExpensesPaid = Math.min(savings, config.otherExpenses);
    savings -= otherExpensesPaid;
    const funSpending = Math.min(savings, funAllocations[month - 1]);
    savings -= funSpending;

    const missedRent = rentPaid < config.rent;
    const missedOtherExpenses = otherExpensesPaid < config.otherExpenses;
    const foodShortage = missedOtherExpenses;
    let happinessChange = funSpending - config.funBaseline;
    if (funSpending === 0) happinessChange -= config.noFunHappinessLoss;
    if (missedRent) happinessChange -= config.missedRentHappinessLoss;
    if (missedOtherExpenses) happinessChange -= config.missedOtherExpensesHappinessLoss;
    if (foodShortage) happinessChange -= config.foodShortageHappinessLoss;
    if (event) happinessChange -= config.badFortuneHappinessLoss;
    happiness += happinessChange;

    months.push({
      month, hours, income, gift, event, jobLost, rentPaid, otherExpensesPaid,
      funSpending, savings, happinessChange, happiness, missedRent,
      missedOtherExpenses, foodShortage,
    });
  }

  const averageHappiness = happiness / MONTHS;
  return {
    months,
    endingSavings: savings,
    averageHappiness,
    qualityOfLife: clamp(50 + averageHappiness / 4, 0, 100),
    badFortunes,
  };
}
