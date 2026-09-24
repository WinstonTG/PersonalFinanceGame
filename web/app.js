import { MONTHS, runPlan } from "./simulation.js";

const form = document.querySelector("#plan-form");
const monthsGrid = document.querySelector("#months-grid");
const investmentInput = document.querySelector("#investment");
const nameInput = document.querySelector("#plan-name");
const results = document.querySelector("#results");
const emptyState = document.querySelector("#empty-state");
const errorMessage = document.querySelector("#form-error");

const money = (value) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
}).format(value);
const signed = (value) => (value >= 0 ? "+" : "−") + money(Math.abs(value));

function monthEditor(month) {
  const wrapper = document.createElement("label");
  wrapper.className = "month-card";
  wrapper.innerHTML =
    '<span class="month-number">' + String(month).padStart(2, "0") + '</span>' +
    '<span class="month-name">Month ' + month + '</span>' +
    '<span class="fun-value" data-value>' + money(150) + '</span>' +
    '<input type="range" min="0" max="400" step="10" value="150" aria-label="Fun spending for month ' + month + '" data-month="' + month + '">' +
    '<span class="range-labels"><span>$0</span><span>$400</span></span>';
  const range = wrapper.querySelector("input");
  const value = wrapper.querySelector("[data-value]");
  range.addEventListener("input", () => { value.textContent = money(Number(range.value)); });
  return wrapper;
}

for (let month = 1; month <= MONTHS; month += 1) monthsGrid.append(monthEditor(month));

function renderResults(simulation, planName) {
  emptyState.hidden = true;
  results.hidden = false;
  document.querySelector("#result-plan-name").textContent = planName || "Your plan";
  document.querySelector("#ending-savings").textContent = money(simulation.endingSavings);
  document.querySelector("#investment-balance").textContent = money(simulation.investmentBalance);
  document.querySelector("#average-happiness").textContent = simulation.averageHappiness.toFixed(0) + " pts";
  document.querySelector("#total-score").textContent = simulation.score.toFixed(0) + " pts";
  document.querySelector("#quality-value").textContent = simulation.qualityOfLife.toFixed(0) + "%";
  document.querySelector("#quality-bar").style.width = simulation.qualityOfLife + "%";
  document.querySelector("#event-count").textContent = simulation.badFortunes + " / 2 bad fortune events";

  document.querySelector("#month-results").innerHTML = simulation.months.map((month) => {
    const flags = [month.event, month.jobLost ? "No income" : "", month.foodShortage ? "Food shortage" : ""]
      .filter(Boolean).join(" · ");
    return '<tr>' +
      '<td><strong>' + month.month + '</strong></td>' +
      '<td>' + month.hours + ' hrs/wk</td>' +
      '<td>' + money(month.income + month.gift) + '</td>' +
      '<td>' + money(month.investmentAmount) + '</td>' +
      '<td>' + money(month.funSpending) + '</td>' +
      '<td class="' + (month.savings < 1000 ? "warning" : "positive") + '">' + money(month.savings) + '</td>' +
      '<td class="' + (month.happinessChange < 0 ? "negative" : "positive") + '">' + signed(month.happinessChange) + '</td>' +
      '<td>' + (flags || "Steady month") + '</td>' +
      '</tr>';
  }).join("");
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  errorMessage.hidden = true;
  try {
    const allocations = [...monthsGrid.querySelectorAll("input")].map((input) => Number(input.value));
    renderResults(runPlan(allocations, Number(investmentInput.value)), nameInput.value.trim());
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  }
});
