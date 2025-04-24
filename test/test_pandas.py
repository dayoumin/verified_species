import pandas as pd

def verify_scientific_names(excel_file, column_name="학명"):
    try:
        df = pd.read_excel(excel_file)
        if column_name not in df.columns:
            print(f"Error: Column '{column_name}' not found.")
            return

        print(f"Verifying names in '{column_name}':")
        for i, name in df[column_name].items():
            print(f"{i}: {name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_scientific_names("marine_species_5.xlsx")
