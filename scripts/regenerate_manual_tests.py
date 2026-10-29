"""
Regenerates side-by-side composite sheets and complete architectural documentation
for manual test directories in output/manual_test/.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline_runner import run_generation_pipeline

TEST_SUITES = [
    # 3 Marla test cases
    ("output/manual_test/3m_plan1", "3 Marla 2-storey house with 3 bedrooms, 3 baths, lounge, kitchen, and drawing room"),
    ("output/manual_test/3m_plan2", "3 Marla modern 2-storey house with 3 bedrooms and 3 baths"),
    ("output/manual_test/3m_plan3", "3 Marla G+1 residence with 3 bedrooms, attached baths, kitchen and lounge"),

    # 5 Marla test cases
    ("output/manual_test/5m_plan1", "5 Marla 2-storey house with 3 bedrooms, 3 baths, lounge, kitchen, and drawing room"),
    ("output/manual_test/5m_plan2", "5 Marla modern 2-storey house with 3 bedrooms and 3 baths"),
    ("output/manual_test/5m_plan3", "5 Marla G+1 residence with 3 bedrooms, attached baths, kitchen and lounge"),

    # 7 Marla test cases
    ("output/manual_test/7m_plan1", "7 Marla 2-storey house with 4 bedrooms, 4 baths, lounge, kitchen, and drawing room"),
    ("output/manual_test/7m_plan2", "7 Marla modern 2-storey house with 4 bedrooms and 4 baths"),
    ("output/manual_test/7m_plan3", "7 Marla G+1 residence with 4 bedrooms, attached baths, kitchen and lounge"),

    # 1 Kanal test cases
    ("output/manual_test/1k_plan1", "1 Kanal 2-storey luxury villa with 4 bedrooms, 4 baths, double kitchen, servant quarter, and lawn"),
    ("output/manual_test/1k_plan2", "1 Kanal palatial 2-storey residence with 4 bedrooms, 5 baths, and garden"),
    ("output/manual_test/1k_plan3", "1 Kanal modern 2-storey estate with 4 bedrooms, 4 baths, and lawn"),
]


def main():
    print("=" * 80)
    print("RE-GENERATING COMPOSITE TWO-FLOOR SHEETS FOR MANUAL TEST CASES")
    print("=" * 80)

    for out_dir, prompt in TEST_SUITES:
        print(f"\n>>> Processing: {out_dir}")
        print(f"    Prompt: '{prompt}'")
        os.makedirs(out_dir, exist_ok=True)
        try:
            plan = run_generation_pipeline(
                prompt=prompt,
                output_dir=out_dir,
                render_3d=False,
                export_format="all"
            )
            if plan:
                print(f"    -> [SUCCESS] Generated {plan.metadata.plan_id} ({plan.metadata.floor_count} floors)")
            else:
                print(f"    -> [FAILED] Pipeline returned None")
        except Exception as e:
            print(f"    -> [EXCEPTION] {e}")

    print("\n" + "=" * 80)
    print("ALL COMPOSITE SHEETS RE-GENERATED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
