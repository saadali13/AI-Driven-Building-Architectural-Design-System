import { CostEstimate, CostBreakdown } from '../types';

export interface CostCalculationParams {
  projectId: string;
  projectTitle: string;
  coveredAreaSqFt: number;
  floors: number;
  category: 'economy' | 'standard' | 'premium' | 'luxury';
  city: 'Islamabad/Rawalpindi' | 'Lahore' | 'Karachi' | 'Peshawar' | 'Multan' | 'Faisalabad';
  currency?: 'PKR' | 'USD';
}

const CITY_FACTORS: Record<string, number> = {
  'Islamabad/Rawalpindi': 1.03,
  'Lahore': 1.00,
  'Karachi': 1.05,
  'Peshawar': 0.96,
  'Multan': 0.95,
  'Faisalabad': 0.94,
};

const BASE_RATE_PER_SQFT: Record<string, { grey: number; finishing: number }> = {
  economy: { grey: 2900, finishing: 2300 }, // Total ~5,200 PKR/sqft
  standard: { grey: 3200, finishing: 3400 }, // Total ~6,600 PKR/sqft
  premium: { grey: 3500, finishing: 4500 }, // Total ~8,000 PKR/sqft
  luxury: { grey: 3900, finishing: 6500 },  // Total ~10,400 PKR/sqft
};

export function calculatePreliminaryCost(params: CostCalculationParams): CostEstimate {
  const {
    projectId,
    projectTitle,
    coveredAreaSqFt,
    floors,
    category,
    city,
    currency = 'PKR',
  } = params;

  const cityFactor = CITY_FACTORS[city] || 1.0;
  const rates = BASE_RATE_PER_SQFT[category] || BASE_RATE_PER_SQFT.standard;

  const adjustedGreyRate = Math.round(rates.grey * cityFactor);
  const adjustedFinishingRate = Math.round(rates.finishing * cityFactor);
  const totalRatePerSqFt = adjustedGreyRate + adjustedFinishingRate;

  const totalCost = Math.round(coveredAreaSqFt * totalRatePerSqFt);
  const greyStructureTotal = Math.round(coveredAreaSqFt * adjustedGreyRate);
  const finishingTotal = totalCost - greyStructureTotal;

  // Breakdown percentages based on standard Pakistan engineering practice (PEC guidelines)
  const breakdown: CostBreakdown = {
    greyStructure: greyStructureTotal,
    foundationAndEarthwork: Math.round(greyStructureTotal * 0.18),
    brickworkMasonry: Math.round(greyStructureTotal * 0.22),
    cementSandCrush: Math.round(greyStructureTotal * 0.26),
    steelRebar: Math.round(greyStructureTotal * 0.34),
    plumbingSanitary: Math.round(finishingTotal * 0.12),
    electricalWiringConduits: Math.round(finishingTotal * 0.14),
    flooringTilesMarbles: Math.round(finishingTotal * 0.24),
    doorsWindowsWoodMetal: Math.round(finishingTotal * 0.22),
    paintFinishingFalseCeiling: Math.round(finishingTotal * 0.14),
    kitchenBathFixtures: Math.round(finishingTotal * 0.14),
    labourCost: Math.round(totalCost * 0.22),
    contingencyAllowance: Math.round(totalCost * 0.05),
  };

  const scenarioMin = Math.round(totalCost * 0.92);
  const scenarioTypical = totalCost;
  const scenarioMax = Math.round(totalCost * 1.14);

  return {
    id: `est_${Date.now()}`,
    projectId,
    projectTitle,
    coveredAreaSqFt,
    floors,
    category,
    regionalCity: city,
    currency,
    ratesDate: 'October 2026',
    breakdown,
    totalEstimatedCostPKR: totalCost,
    costPerSqFtPKR: totalRatePerSqFt,
    scenarioMinPKR: scenarioMin,
    scenarioTypicalPKR: scenarioTypical,
    scenarioMaxPKR: scenarioMax,
    notes: [
      `Cost model configured for ${city} regional market index (Factor ${cityFactor}x).`,
      `Finishing category: ${category.toUpperCase()} specifications with grade-60 steel reinforcement.`,
      `Contingency margin (+5%) incorporated to guard against short-term material inflation.`,
      `Does not include society approval fees, plot acquisition costs, or high-voltage transformer installations.`,
    ],
    createdAt: new Date().toISOString().split('T')[0],
  };
}

export function formatPKR(val: number): string {
  if (val >= 10000000) {
    const crores = (val / 10000000).toFixed(2);
    return `PKR ${crores} Crore`;
  }
  if (val >= 100000) {
    const lakhs = (val / 100000).toFixed(2);
    return `PKR ${lakhs} Lakh`;
  }
  return `PKR ${val.toLocaleString('en-PK')}`;
}
