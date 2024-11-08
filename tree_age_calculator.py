import argparse
import math
from datetime import datetime

# Species-specific constants from the table for use in growth calculations
species_data = {
    "White pine":     {"mean_bai": 13.4,  "linear_coeff": 13.6, "curvature_coeff":  0.28, "s": 6.9, "n":  511,  "w": .101},
    "Hemlock":        {"mean_bai":  9.7,  "linear_coeff":  9.9, "curvature_coeff": -0.07, "s": 5.6, "n":  450,  "w": .146},
    "Yellow birch":   {"mean_bai":  8.8,  "linear_coeff": 12.1, "curvature_coeff": -0.27, "s": 5.2, "n":  183,  "w": .159},
    "Red spruce":     {"mean_bai":  8.5,  "linear_coeff": -5.7, "curvature_coeff": -0.93, "s": 4.9, "n": 2302,  "w": .160},
    "Red oak":        {"mean_bai":  8.1,  "linear_coeff": 10.8, "curvature_coeff":  0.19, "s": 4.0, "n":  379,  "w": .158},
    "Sugar maple":    {"mean_bai":  8.0,  "linear_coeff": 11.7, "curvature_coeff":  0.14, "s": 4.1, "n":  338,  "w": .162},
    "Balsam fir":     {"mean_bai":  7.7,  "linear_coeff": -1.5, "curvature_coeff": -1.72, "s": 3.6, "n":  359,  "w": .163},
    "White ash":      {"mean_bai":  7.6,  "linear_coeff":  9.6, "curvature_coeff":  0.59, "s": 4.5, "n":  143,  "w": .179},
    "American beech": {"mean_bai":  6.7,  "linear_coeff": 25.2, "curvature_coeff":  0.64, "s": 3.4, "n":  137,  "w": .203},
    "Red maple":      {"mean_bai":  6.7,  "linear_coeff":  1.8, "curvature_coeff":  0.33, "s": 3.4, "n":  296,  "w": .192}
}

def calculate_weighting_factor(species):
    """Calculate weighting factor W using harmonic mean of BAI values."""
    species_info = species_data[species]
    # n = species_info["n"]
    # mean_bai = species_info["mean_bai"]
    # return (1 / n) * sum(1 / mean_bai for _ in range(n))
    return species_info["w"]

def calculate_growth_rate(species, year):
    """Calculate growth rate based on year. We only have 1950-1980 for data, so we just apply the end points beyond that."""
    if year < 1950:
        year = 1950
    elif year > 1980:
        year = 1980
    
    species_info = species_data[species]
    mean_bai = species_info["mean_bai"]
    linear_coeff = species_info["linear_coeff"] / 1000.0
    curvature_coeff = species_info["curvature_coeff"] / 1000.0
    year_normalized = year - 1965
    w = calculate_weighting_factor(species)
    
    # Mean growth curve formula
    growth_rate = mean_bai + (year * linear_coeff / w) + ((year_normalized**2 - 80) * curvature_coeff / w)
    return max(growth_rate, 0)  # Ensure growth rate is non-negative

def integrate_growth_curve(species, circumference_cm):
    """Integrate growth over the years to estimate age based on observed circumference."""
    radius_cm = circumference_cm / (2 * math.pi)
    area_target = math.pi * (radius_cm ** 2)  # Target basal area based on radius
    cumulative_area = 0
    year = datetime.now().year  # Start at current year and work backward
    age = 0
    
    # Periodic printing every 10 years
    print_interval = 10
    
    while cumulative_area < area_target:
        growth_rate = calculate_growth_rate(species, year)
        cumulative_area += growth_rate
        year -= 1
        age += 1

        # Print progress at intervals
        # if age % print_interval == 0:
        #     print(f"Year: {year}, Age estimate: {age} years, Cumulative area: {cumulative_area:.2f}, Target area: {area_target:.2f}")

    return age, year

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Calculate the estimated age of a tree based on its species, circumference, "
            "and environmental conditions.\n\n"
            "To measure the tree's circumference, measure at 'breast height' (1.4 meters or 4.5 feet above the ground):\n"
            "1. Select a spot 1.4 meters up from the base of the tree.\n"
            "2. Wrap a flexible measuring tape around the tree at this height, keeping it straight and snug.\n"
            "3. Record the circumference in centimeters.\n\n"
            "Supported species include:\n"
            "- White pine\n"
            "- Hemlock\n"
            "- Yellow birch\n"
            "- Red spruce\n"
            "- Red oak\n"
            "- Sugar maple\n"
            "- Balsam fir\n"
            "- White ash\n"
            "- American beech\n"
            "- Red maple\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("species", type=str, help="Species of the tree (e.g., 'Red spruce', 'White pine')")
    parser.add_argument("circumference_cm", type=float, help="Circumference of the tree in centimeters")
    parser.add_argument("--winter_temp", type=float, default=-2, help="Average winter temperature in degrees Celsius (default: -2°C)")
    parser.add_argument("--summer_temp", type=float, default=21, help="Average summer temperature in degrees Celsius (default: 21°C)")
    parser.add_argument("--elevation", type=float, default=56, help="Elevation in meters (default: 56m)")
    parser.add_argument("--soil_type", type=str, default="loamy", choices=["loamy", "sandy", "rocky"],
                        help="Soil type around the tree (default: loamy)")

    args = parser.parse_args()

    try:
        age, year = integrate_growth_curve(args.species, args.circumference_cm)
        print(f"The estimated age of the {args.species} tree is approximately {age} years.\nIt was planted in approximately {year}.")
    except ValueError as e:
        print(e)
