from __future__ import annotations

from src.analytics.powerbi import export_powerbi_model


def main() -> None:
    exported = export_powerbi_model()
    print("Power BI export complete.")
    for table, path in exported.items():
        print(f"{table}: {path}")


if __name__ == "__main__":
    main()
