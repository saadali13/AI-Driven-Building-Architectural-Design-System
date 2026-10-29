/**
 * Seeds baseline PKR material catalog aligned with the ArchAI Cost Estimator UI.
 * Run: npm run db:seed
 */
import { PrismaClient, MaterialCategory } from '@prisma/client';

const prisma = new PrismaClient();

const materials = [
  {
    name: 'Portland Cement (50kg)',
    category: MaterialCategory.CEMENT,
    unit: 'bag',
    unitPricePkr: 1105,
    supplier: 'Local distributor',
  },
  {
    name: 'Grade 60 Steel Rebar',
    category: MaterialCategory.STEEL,
    unit: 'ton',
    unitPricePkr: 945000,
    supplier: 'Steel mill',
  },
  {
    name: 'First Class Bricks',
    category: MaterialCategory.BRICKS,
    unit: '1000_units',
    unitPricePkr: 810000,
    supplier: 'Kiln supplier',
  },
  {
    name: 'Construction Labor',
    category: MaterialCategory.LABOR,
    unit: 'project',
    unitPricePkr: 590000,
    supplier: 'Contractor',
  },
  {
    name: 'Italian Marble',
    category: MaterialCategory.STONE,
    unit: 'sqft',
    unitPricePkr: 850,
    supplier: 'Imported finishing',
  },
  {
    name: 'Walnut Hardwood',
    category: MaterialCategory.WOOD,
    unit: 'sqft',
    unitPricePkr: 620,
    supplier: 'Local carpentry',
  },
  {
    name: 'Stone Cladding',
    category: MaterialCategory.STONE,
    unit: 'sqft',
    unitPricePkr: 480,
    supplier: 'Facade supplier',
  },
  {
    name: 'Acoustic Glass',
    category: MaterialCategory.GLASS,
    unit: 'sqft',
    unitPricePkr: 1250,
    supplier: 'Glazing vendor',
  },
];

async function main() {
  let created = 0;

  for (const material of materials) {
    const existing = await prisma.material.findFirst({
      where: { name: material.name },
    });

    if (existing) {
      await prisma.material.update({
        where: { id: existing.id },
        data: material,
      });
    } else {
      await prisma.material.create({ data: material });
      created += 1;
    }
  }

  console.log(`Seed complete — ${created} new material(s), ${materials.length} total processed.`);
}

main()
  .catch((error) => {
    console.error('Seed failed:', error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
