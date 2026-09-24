export const MONTHS = 12;
export const SHARED_SEED = 20260924;

export const DEFAULTS = Object.freeze({
  startingSavings: 3000, hourlyWage: 15, rent: 1000, otherExpenses: 125,
  minHours: 25, maxHours: 35, weeksPerMonth: 4, maxFun: 400,
  maxInvestment: 500, investmentMonthlyReturn: 0.008,
  giftAmount: 50, giftChance: 0.5, badFortuneChance: 0.1,
  maxBadFortunes: 2, badFortuneMoneyLoss: 200, badFortuneHappinessLoss: 35,
  jobLossChance: 0.5, funHappinessScale: 400, funHappinessDecay: 150,
  noFunHappinessLoss: 50, missedRentHappinessLoss: 500,
  missedOtherExpensesHappinessLoss: 300,
});

export function createSeededRandom(seed = SHARED_SEED) {
  let value = Math.abs(Number(seed) || SHARED_SEED) % 2147483647;
  return () => {
    value = (value * 16807) % 2147483647;
    return (value - 1) / 2147483646;
  };
}
export function funHappiness(funSpending, config = DEFAULTS) {
  return config.funHappinessScale * (1 - Math.exp(-funSpending / config.funHappinessDecay));
}

export function runPlan(funAllocations, investmentAmount = 0, { seed = SHARED_SEED, config = DEFAULTS } = {}) {
  if (!Array.isArray(funAllocations) || funAllocations.length !== MONTHS) {
    throw new Error("Your plan needs 12 monthly fun allocations.");
  }
  if (funAllocations.some((value) => !Number.isFinite(value) || value < 0 || value > config.maxFun)) {
    throw new Error("Each fun allocation must be between $0 and $" + config.maxFun + ".");
  }
  if (!Number.isFinite(investmentAmount) || investmentAmount < 0 || investmentAmount > config.maxInvestment) {
    throw new Error("Monthly investment must be between $0 and $" + config.maxInvestment + ".");
  }

  const random = createSeededRandom(seed);
  const randomInt = (min, max) => Math.floor(random() * (max - min + 1)) + min;
  let savings = config.startingSavings;
  let investmentBalance = 0;
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
    const missedRent = rentPaid < config.rent;
    const missedOtherExpenses = otherExpensesPaid < config.otherExpenses;

    const investmentAmountForMonth = Math.min(savings, investmentAmount);
    savings -= investmentAmountForMonth;
    investmentBalance += investmentAmountForMonth;
    const funSpending = Math.min(savings, funAllocations[month - 1]);
    savings -= funSpending;
    investmentBalance *= 1 + config.investmentMonthlyReturn;

    let happinessChange = funHappiness(funSpending, config);
    if (funAllocations[month - 1] === 0) happinessChange -= config.noFunHappinessLoss;
    if (missedRent) happinessChange -= config.missedRentHappinessLoss;
    if (missedOtherExpenses) happinessChange -= config.missedOtherExpensesHappinessLoss;
    if (event) happinessChange -= config.badFortuneHappinessLoss;
    happiness += happinessChange;

    months.push({
      month, hours, income, gift, event, jobLost, rentPaid, otherExpensesPaid,
      requestedInvestment: investmentAmount, investmentAmount: investmentAmountForMonth,
      investmentBalance, requestedFun: funAllocations[month - 1], funSpending,
      savings, happinessChange, happiness, missedRent, missedOtherExpenses,
      foodShortage: missedOtherExpenses,
    });
  }

  const averageHappiness = happiness / MONTHS;
  return {
    months, endingSavings: savings, investmentBalance, averageHappiness,
    totalHappiness: happiness, score: savings + investmentBalance + happiness,
    qualityOfLife: Math.min(100, Math.max(0, 50 + averageHappiness / 8)),
    badFortunes,
  };
}
