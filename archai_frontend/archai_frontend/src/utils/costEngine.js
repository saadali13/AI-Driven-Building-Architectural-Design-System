/**
 * ArchAI Studio — Location-Aware Construction Cost Calculation & Geolocation Engine
 * Enterprise Rate Index & Municipal By-Laws for Pakistan & Global Construction Markets
 */

export const REGIONAL_MARKETS = {
  islamabad: {
    key: 'islamabad',
    city: 'Islamabad',
    region: 'Federal Capital',
    country: 'Pakistan',
    authority: 'Capital Development Authority (CDA)',
    coordinates: { lat: 33.6844, lng: 73.0479 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 2B (Moderate-High)',
    bylaws: {
      maxGroundCoveragePct: 65,
      maxHeightFt: 35,
      frontSetbackFt: 10,
      rearSetbackFt: 5,
      sideSetbackFt: 4,
      farRatio: '1:1.6',
      rainwaterHarvesting: true
    },
    materials: {
      cementBagPkr: 1420,        // Fauji / Bestway 50kg OPC
      steelTonPkr: 265000,       // Mughal / Amreli Grade 60 Rebar
      bricksPer1000Pkr: 14200,   // Potohar Kiln First-Class Red Clay
      sandPer100CftPkr: 4800,    // Margalla Clean Pit Sand
      crushPer100CftPkr: 5200,   // Margalla Limestone 1/2" Aggregate
      laborSqFtPkr: 480,         // Master Mason & Civil Laborers
      mepSqFtPkr: 320,           // Electrical & Plumbing Conduit
      finishingBaseSqFt: 650     // Standard Tile, Joinery & Paint
    }
  },
  rawalpindi: {
    key: 'rawalpindi',
    city: 'Rawalpindi',
    region: 'Punjab',
    country: 'Pakistan',
    authority: 'Rawalpindi Development Authority (RDA) / Bahria / DHA',
    coordinates: { lat: 33.5651, lng: 73.0169 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 2B (Moderate)',
    bylaws: {
      maxGroundCoveragePct: 70,
      maxHeightFt: 38,
      frontSetbackFt: 8,
      rearSetbackFt: 5,
      sideSetbackFt: 0,
      farRatio: '1:1.75',
      rainwaterHarvesting: false
    },
    materials: {
      cementBagPkr: 1410,
      steelTonPkr: 264000,
      bricksPer1000Pkr: 13900,
      sandPer100CftPkr: 4700,
      crushPer100CftPkr: 5100,
      laborSqFtPkr: 460,
      mepSqFtPkr: 310,
      finishingBaseSqFt: 620
    }
  },
  lahore: {
    key: 'lahore',
    city: 'Lahore',
    region: 'Punjab',
    country: 'Pakistan',
    authority: 'Lahore Development Authority (LDA) / DHA Lahore',
    coordinates: { lat: 31.5204, lng: 74.3587 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 2A (Low-Moderate)',
    bylaws: {
      maxGroundCoveragePct: 65,
      maxHeightFt: 40,
      frontSetbackFt: 10,
      rearSetbackFt: 5,
      sideSetbackFt: 5,
      farRatio: '1:1.6',
      rainwaterHarvesting: true
    },
    materials: {
      cementBagPkr: 1390,        // Maple Leaf / DG Cement
      steelTonPkr: 262000,       // Ittefaq / Mughal Rebar
      bricksPer1000Pkr: 13200,   // Chenab Kiln First-Class
      sandPer100CftPkr: 4200,    // Ravi Sand
      crushPer100CftPkr: 4900,    // Sargodha Black Stone Aggregate
      laborSqFtPkr: 450,
      mepSqFtPkr: 300,
      finishingBaseSqFt: 610
    }
  },
  karachi: {
    key: 'karachi',
    city: 'Karachi',
    region: 'Sindh',
    country: 'Pakistan',
    authority: 'Sindh Building Control Authority (SBCA) / Cantonment',
    coordinates: { lat: 24.8607, lng: 67.0011 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 2B + Coastal Marine Corrosion',
    bylaws: {
      maxGroundCoveragePct: 70,
      maxHeightFt: 42,
      frontSetbackFt: 8,
      rearSetbackFt: 6,
      sideSetbackFt: 4,
      farRatio: '1:1.8',
      rainwaterHarvesting: false
    },
    materials: {
      cementBagPkr: 1470,        // Thatta / Lucky Anti-Sulphate
      steelTonPkr: 272000,       // Razmak / Amreli Marine Rebar
      bricksPer1000Pkr: 14800,   // Solid Clay / Hollow Concrete
      sandPer100CftPkr: 5200,    // Hub River Washed Sand
      crushPer100CftPkr: 5600,    // Nooriabad Hard Rock Aggregate
      laborSqFtPkr: 510,
      mepSqFtPkr: 340,
      finishingBaseSqFt: 680
    }
  },
  peshawar: {
    key: 'peshawar',
    city: 'Peshawar',
    region: 'Khyber Pakhtunkhwa',
    country: 'Pakistan',
    authority: 'Peshawar Development Authority (PDA)',
    coordinates: { lat: 34.0151, lng: 71.5249 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 3 (High Seismic Demand)',
    bylaws: {
      maxGroundCoveragePct: 65,
      maxHeightFt: 35,
      frontSetbackFt: 10,
      rearSetbackFt: 5,
      sideSetbackFt: 5,
      farRatio: '1:1.5',
      rainwaterHarvesting: false
    },
    materials: {
      cementBagPkr: 1380,        // Cherat Cement
      steelTonPkr: 268000,       // Frontier / Mughal Rebar
      bricksPer1000Pkr: 13500,
      sandPer100CftPkr: 4400,
      crushPer100CftPkr: 4800,
      laborSqFtPkr: 440,
      mepSqFtPkr: 290,
      finishingBaseSqFt: 590
    }
  },
  faisalabad: {
    key: 'faisalabad',
    city: 'Faisalabad',
    region: 'Punjab',
    country: 'Pakistan',
    authority: 'Faisalabad Development Authority (FDA)',
    coordinates: { lat: 31.4504, lng: 73.1350 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 2A (Low-Moderate)',
    bylaws: {
      maxGroundCoveragePct: 68,
      maxHeightFt: 38,
      frontSetbackFt: 8,
      rearSetbackFt: 5,
      sideSetbackFt: 4,
      farRatio: '1:1.6',
      rainwaterHarvesting: false
    },
    materials: {
      cementBagPkr: 1395,
      steelTonPkr: 263000,
      bricksPer1000Pkr: 12900,
      sandPer100CftPkr: 4100,
      crushPer100CftPkr: 4850,
      laborSqFtPkr: 435,
      mepSqFtPkr: 295,
      finishingBaseSqFt: 595
    }
  },
  multan: {
    key: 'multan',
    city: 'Multan',
    region: 'Punjab',
    country: 'Pakistan',
    authority: 'Multan Development Authority (MDA)',
    coordinates: { lat: 30.1575, lng: 71.5249 },
    currency: 'PKR',
    currencySymbol: '₨',
    seismicZone: 'Zone 2A (Low)',
    bylaws: {
      maxGroundCoveragePct: 68,
      maxHeightFt: 36,
      frontSetbackFt: 9,
      rearSetbackFt: 5,
      sideSetbackFt: 4,
      farRatio: '1:1.6',
      rainwaterHarvesting: false
    },
    materials: {
      cementBagPkr: 1405,
      steelTonPkr: 264500,
      bricksPer1000Pkr: 12800,
      sandPer100CftPkr: 4000,
      crushPer100CftPkr: 4950,
      laborSqFtPkr: 430,
      mepSqFtPkr: 290,
      finishingBaseSqFt: 585
    }
  },
  dubai: {
    key: 'dubai',
    city: 'Dubai',
    region: 'Dubai Emirate',
    country: 'United Arab Emirates',
    authority: 'Dubai Municipality / Trakhees (Al Sa\'fat Green Code)',
    coordinates: { lat: 25.2048, lng: 55.2708 },
    currency: 'AED',
    currencySymbol: 'AED ',
    seismicZone: 'Zone 2A (International)',
    bylaws: {
      maxGroundCoveragePct: 60,
      maxHeightFt: 45,
      frontSetbackFt: 12,
      rearSetbackFt: 8,
      sideSetbackFt: 6,
      farRatio: '1:1.4',
      rainwaterHarvesting: false
    },
    materials: {
      cementBagPkr: 45,
      steelTonPkr: 2950,
      bricksPer1000Pkr: 1800,
      sandPer100CftPkr: 220,
      crushPer100CftPkr: 280,
      laborSqFtPkr: 45,
      mepSqFtPkr: 38,
      finishingBaseSqFt: 110
    }
  }
};

/**
 * Standard Preset 2D Floor Plan Matrices
 */
export const FLOOR_PLAN_PRESETS = [
  {
    id: '5marla',
    label: '5 Marla Contemporary Villa',
    plotMarla: 5.0,
    plotSqFt: 1125,
    coveredAreaSqFt: 2250,
    carpetAreaSqFt: 1840,
    floors: 2,
    bedCount: 3,
    bathCount: 3,
    dimensions: '25 ft × 45 ft',
    description: 'Ground + 1st floor layout with 3 bedrooms, open lounge, kitchen, and balcony.'
  },
  {
    id: '10marla',
    label: '10 Marla Dual Family Residence',
    plotMarla: 10.0,
    plotSqFt: 2250,
    coveredAreaSqFt: 4200,
    carpetAreaSqFt: 3550,
    floors: 2,
    bedCount: 5,
    bathCount: 5,
    dimensions: '35 ft × 65 ft',
    description: 'Double unit duplex layout with separate servant quarter, 2 drawing rooms & terrace.'
  },
  {
    id: '1kanal',
    label: '1 Kanal Luxury Executive Estate',
    plotMarla: 20.0,
    plotSqFt: 4500,
    coveredAreaSqFt: 6800,
    carpetAreaSqFt: 5800,
    floors: 2,
    bedCount: 6,
    bathCount: 7,
    dimensions: '50 ft × 90 ft',
    description: 'Sprawling luxury architectural estate with central courtyard, basement & swimming pool.'
  }
];

export const SPEC_TIERS = {
  0: {
    id: 'ECONOMY',
    label: 'Economy Grade',
    desc: 'Cost-effective local materials, standard cement, local ceramic tiles, functional finishes.',
    cementFactor: 0.38,
    steelFactor: 3.6,
    bricksFactor: 15.0,
    sandFactor: 0.55,
    crushFactor: 0.65,
    laborMultiplier: 0.90,
    mepMultiplier: 0.85,
    finishingMultiplier: 0.75
  },
  1: {
    id: 'STANDARD',
    label: 'Standard Premium',
    desc: 'Grade 60 steel rebar, premium OPC cement, imported porcelain floor tiles, Ash wood doors.',
    cementFactor: 0.44,
    steelFactor: 4.2,
    bricksFactor: 17.5,
    sandFactor: 0.65,
    crushFactor: 0.75,
    laborMultiplier: 1.0,
    mepMultiplier: 1.0,
    finishingMultiplier: 1.0
  },
  2: {
    id: 'LUXURY',
    label: 'Executive Luxury',
    desc: 'Full cantilever structural framing, Spanish granite, smart home automation, high-end Sanitary.',
    cementFactor: 0.50,
    steelFactor: 4.8,
    bricksFactor: 19.0,
    sandFactor: 0.75,
    crushFactor: 0.85,
    laborMultiplier: 1.25,
    mepMultiplier: 1.45,
    finishingMultiplier: 1.65
  }
};

/**
 * High-precision Haversine Distance matching
 */
export function findNearestMarket(lat, lng) {
  let closest = 'islamabad';
  let minDist = Infinity;

  const toRad = (v) => (v * Math.PI) / 180;
  const R = 6371; // km

  for (const [key, market] of Object.entries(REGIONAL_MARKETS)) {
    const dLat = toRad(market.coordinates.lat - lat);
    const dLon = toRad(market.coordinates.lng - lng);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(lat)) *
        Math.cos(toRad(market.coordinates.lat)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const dist = R * c;

    if (dist < minDist) {
      minDist = dist;
      closest = key;
    }
  }

  return closest;
}

/**
 * Main Dynamic Calculation Engine
 */
export function calculateCostMatrix({
  locationKey = 'islamabad',
  tierIndex = 1,
  coveredAreaSqFt = 2250,
  plotMarla = 5.0,
  numFloors = 2,
  contingencyPct = 5.0
}) {
  const market = REGIONAL_MARKETS[locationKey] || REGIONAL_MARKETS.islamabad;
  const rates = market.materials;
  const tSpec = SPEC_TIERS[tierIndex] || SPEC_TIERS[1];
  const area = Math.max(500, Number(coveredAreaSqFt));

  // 1. Material Quantities & Structural Costs
  const totalCementBags = Math.ceil(area * tSpec.cementFactor);
  const cementCost = totalCementBags * rates.cementBagPkr;

  const totalSteelKg = area * tSpec.steelFactor;
  const totalSteelTons = Number((totalSteelKg / 1000).toFixed(3));
  const steelCost = totalSteelTons * rates.steelTonPkr;

  const totalBricks = Math.ceil(area * tSpec.bricksFactor);
  const bricksCost = (totalBricks / 1000) * rates.bricksPer1000Pkr;

  const totalSandCft = Math.round(area * tSpec.sandFactor);
  const sandCost = (totalSandCft / 100) * rates.sandPer100CftPkr;

  const totalCrushCft = Math.round(area * tSpec.crushFactor);
  const crushCost = (totalCrushCft / 100) * rates.crushPer100CftPkr;

  // 2. Civil Labor & Formwork Contracts
  const laborCost = Math.round(area * rates.laborSqFtPkr * tSpec.laborMultiplier);

  // 3. Services & MEP (Electrical, Plumbing, Drainage)
  const mepCost = Math.round(area * rates.mepSqFtPkr * tSpec.mepMultiplier);

  // 4. Architectural Finishing Fitout
  const finishingCost = Math.round(area * rates.finishingBaseSqFt * tSpec.finishingMultiplier);

  // Subtotals & Grand Totals
  const greyStructureTotal = Math.round(cementCost + steelCost + bricksCost + sandCost + crushCost + laborCost);
  const subtotal = greyStructureTotal + mepCost + finishingCost;
  const contingencyTotal = Math.round(subtotal * (contingencyPct / 100));
  const grandTotal = subtotal + contingencyTotal;
  const costPerSqFt = Math.round(grandTotal / area);
  const grandTotalMillion = Number((grandTotal / 1000000).toFixed(2));

  // 5. Build Comprehensive Bill of Quantities (BOQ) Items
  const boqItems = [
    {
      id: 'cement',
      category: 'Grey Structure',
      name: 'Portland Cement (50kg Bags)',
      unit: 'Bags',
      unitRate: rates.cementBagPkr,
      quantity: totalCementBags,
      totalCost: cementCost,
      pct: Math.round((cementCost / grandTotal) * 100),
      color: 'bg-blue-600',
      notes: `OPC Grade 53/43 Compliant with ${market.authority} by-laws`
    },
    {
      id: 'steel',
      category: 'Grey Structure',
      name: 'Deformed Rebar Steel (Grade 60)',
      unit: 'Metric Tons',
      unitRate: rates.steelTonPkr,
      quantity: totalSteelTons,
      totalCost: steelCost,
      pct: Math.round((steelCost / grandTotal) * 100),
      color: 'bg-indigo-600',
      notes: `60,000 PSI High-Yield Steel, ${market.seismicZone}`
    },
    {
      id: 'bricks',
      category: 'Grey Structure',
      name: 'First-Class Kiln Clay Bricks',
      unit: 'Pieces',
      unitRate: rates.bricksPer1000Pkr / 1000,
      quantity: totalBricks,
      totalCost: bricksCost,
      pct: Math.round((bricksCost / grandTotal) * 100),
      color: 'bg-amber-500',
      notes: '9x4.5x3 in standard kiln burnt red clay bricks'
    },
    {
      id: 'sand',
      category: 'Grey Structure',
      name: 'River Pit Sand (Plaster & Mortar)',
      unit: 'Cubic Feet (CFT)',
      unitRate: rates.sandPer100CftPkr / 100,
      quantity: totalSandCft,
      totalCost: sandCost,
      pct: Math.round((sandCost / grandTotal) * 100),
      color: 'bg-yellow-600',
      notes: 'Washed silt-free graded sand'
    },
    {
      id: 'crush',
      category: 'Grey Structure',
      name: 'Crushed Coarse Aggregate (1/2" & 3/4")',
      unit: 'Cubic Feet (CFT)',
      unitRate: rates.crushPer100CftPkr / 100,
      quantity: totalCrushCft,
      totalCost: crushCost,
      pct: Math.round((crushCost / grandTotal) * 100),
      color: 'bg-slate-600',
      notes: 'Hard limestone angular gravel for RCC casting'
    },
    {
      id: 'labor',
      category: 'Civil Workforce',
      name: 'Civil Labor & Formwork Contracts',
      unit: 'Sq. Ft',
      unitRate: Math.round(rates.laborSqFtPkr * tSpec.laborMultiplier),
      quantity: area,
      totalCost: laborCost,
      pct: Math.round((laborCost / grandTotal) * 100),
      color: 'bg-emerald-600',
      notes: 'Master Masons, Steel fixers, Shuttering carpenters & Excavation'
    },
    {
      id: 'mep',
      category: 'Services & MEP',
      name: 'Electrical, Plumbing & Piping MEP',
      unit: 'Sq. Ft',
      unitRate: Math.round(rates.mepSqFtPkr * tSpec.mepMultiplier),
      quantity: area,
      totalCost: mepCost,
      pct: Math.round((mepCost / grandTotal) * 100),
      color: 'bg-rose-500',
      notes: 'PPRC Water pipes, PVC drainage & Class-A copper conduits'
    },
    {
      id: 'finishing',
      category: 'Architectural Finishing',
      name: 'Flooring, Tiles, Joinery & Paint Fitouts',
      unit: 'Sq. Ft',
      unitRate: Math.round(rates.finishingBaseSqFt * tSpec.finishingMultiplier),
      quantity: area,
      totalCost: finishingCost,
      pct: Math.round((finishingCost / grandTotal) * 100),
      color: 'bg-purple-600',
      notes: `${tSpec.label} Grade porcelain tiles, Ash wood doors, Weather-resistant paint`
    },
    {
      id: 'contingency',
      category: 'Risk Reserve',
      name: `Inflation & Volatility Buffer (${contingencyPct}%)`,
      unit: 'Fixed Reserve',
      unitRate: contingencyTotal,
      quantity: 1,
      totalCost: contingencyTotal,
      pct: Math.round((contingencyTotal / grandTotal) * 100),
      color: 'bg-cyan-600',
      notes: 'Indexed reserve for fuel/commodity price shifts'
    }
  ];

  // Municipal By-Law Verification
  const plotSqFt = plotMarla * 225;
  const groundFloorArea = area / numFloors;
  const actualCoveragePct = Number(((groundFloorArea / plotSqFt) * 100).toFixed(1));
  const maxAllowedCoveragePct = market.bylaws.maxGroundCoveragePct;

  const bylawsCompliance = {
    authority: market.authority,
    plotMarla,
    plotSqFt,
    actualCoveragePct,
    maxAllowedCoveragePct,
    isCoverageCompliant: actualCoveragePct <= maxAllowedCoveragePct,
    frontSetbackRequiredFt: market.bylaws.frontSetbackFt,
    rearSetbackRequiredFt: market.bylaws.rearSetbackFt,
    sideSetbackRequiredFt: market.bylaws.sideSetbackFt,
    seismicZone: market.seismicZone
  };

  return {
    market,
    tier: tSpec,
    coveredAreaSqFt: area,
    costPerSqFt,
    greyStructureTotal,
    finishingTotal: finishingCost,
    mepTotal: mepCost,
    laborTotal: laborCost,
    contingencyTotal,
    grandTotal,
    grandTotalMillion,
    boqItems,
    bylawsCompliance
  };
}

export function formatCurrency(amount, currency = 'PKR') {
  if (currency === 'AED') {
    return `AED ${Number(amount).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }
  return `₨ ${Number(amount).toLocaleString('en-PK', { maximumFractionDigits: 0 })}`;
}
