# ==========================================
# FILE: run_pipeline.py
# ==========================================

import sys
import config


def usage():
    print("Usage:")
    print("  python run_pipeline.py <stage> <input_file> [city_name] [mode]")
    print("  python run_pipeline.py compare")
    print()
    print("  stage      : extract | abilities | boosts | rankings | report |")
    print("               html | my_city | optimize | all | compare")
    print("  input_file : filename inside data/input/  (not needed for compare)")
    print("  city_name  : label for the output folder (default: parsed from filename)")
    print("  mode       : balanced | GBG | GE | QI  (default: balanced)")
    print()
    print("Examples:")
    print("  python run_pipeline.py all FullMyCityName_Export.json")
    print("  python run_pipeline.py all FullMyCityName_Export_20260501.json")
    print("  python run_pipeline.py all FullMyCityName_Export.json CITY GBG")
    print("  python run_pipeline.py my_city FullMyCityName_Export.json")
    print("  python run_pipeline.py compare")


def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "usage"

    # compare reads existing output folders — no city file needed
    if cmd == "compare":
        import city_compare
        city_compare.run()
        return

    if len(sys.argv) < 3:
        usage()
        sys.exit(1)

    input_file = sys.argv[2]
    city_name  = sys.argv[3] if len(sys.argv) > 3 else None
    mode       = sys.argv[4] if len(sys.argv) > 4 else "balanced"

    run_label = config.configure(input_file, city_name)
    print(f"Run   : {run_label}")
    print(f"Input : {config.INPUT_FILE}")
    print(f"Output: {config.OUTPUT_DIR}")
    print()

    # Import stages after configure() so all config paths are resolved
    from core import extract
    from core import abilities
    from core import boosts
    from core import rankings
    from core import report
    from core import html_report
    from core import my_city
    from core import optimizer

    if cmd == "extract":
        extract.run()

    elif cmd == "abilities":
        abilities.run()

    elif cmd == "boosts":
        boosts.run()

    elif cmd == "rankings":
        rankings.run()

    elif cmd == "report":
        report.run()

    elif cmd == "html":
        html_report.run()

    elif cmd == "my_city":
        my_city.run()

    elif cmd == "optimize":
        optimizer.run(mode=mode)

    elif cmd == "all":
        extract.run()
        abilities.run()
        boosts.run()
        rankings.run()
        report.run()
        my_city.run()
        html_report.run()
        optimizer.run(mode=mode)

    else:
        usage()


if __name__ == "__main__":
    main()
