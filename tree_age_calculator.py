import argparse

# Updated basal area increment (BAI) values per species in cm²/year
growth_rates = {
    "Red Spruce": {"small": 1.5, "medium": 2.5, "large": 1.8},
    "Sugar Maple": {"small": 10.0, "medium": 11.0, "large": 9.0},
    "Yellow Birch": {"small": 10.5, "medium": 11.5, "large": 12.0},
    "American Beech": {"small": 9.0, "medium": 9.5, "large": 10.0},
    "Eastern Hemlock": {"small": 11.0, "medium": 12.0, "large": 13.0},
    "Eastern White Pine": {"small": 17.0, "medium": 19.0, "large": 22.0},
    "Northern Red Oak": {"small": 10.0, "medium": 12.0, "large": 13.0},
    "Balsam Fir": {"small": 9.0, "medium": 10.0, "large": 14.0},
    "White Ash": {"small": 11.0, "medium": 12.0, "large": 13.0},
    "Red Maple": {"small": 9.0, "medium": 10.0, "large": 11.0}
}

def get_diameter_class(diameter_cm):
    if diameter_cm < 20:
        return "small"
    elif 20 <= diameter_cm < 40:
        return "medium"
    else:
        return "large"

def adjust_growth_rate(growth_rate, winter_temp, summer_temp, elevation, tree_age=None, soil_type="loamy"):
    if winter_temp > -5:
        growth_rate *= 1.05
    elif winter_temp < -10:
        growth_rate *= 0.95
    if summer_temp > 25:
        growth_rate *= 0.9
    elif summer_temp < 15:
        growth_rate *= 1.05
    if elevation > 800:
        growth_rate *= 0.85
    elif elevation < 400:
        growth_rate *= 1.05
    if tree_age is not None:
        if tree_age > 50:
            growth_rate *= 0.9
        if tree_age > 100:
            growth_rate *= 0.8
    if soil_type.lower() == "sandy":
        growth_rate *= 0.9
    elif soil_type.lower() == "rocky":
        growth_rate *= 0.85
    return growth_rate

def calculate_tree_age(species, circumference_cm, winter_temp=-2, summer_temp=21, elevation=56, tree_age=None, soil_type="loamy"):
    if species in growth_rates:
        radius_cm = circumference_cm / (2 * 3.14159)
        diameter_cm = 2 * radius_cm
        diameter_class = get_diameter_class(diameter_cm)
        if diameter_class in growth_rates[species]:
            base_growth_rate = growth_rates[species][diameter_class]
            adjusted_growth_rate = adjust_growth_rate(base_growth_rate, winter_temp, summer_temp, elevation, tree_age, soil_type)
            age = (radius_cm ** 2) / adjusted_growth_rate
            return int(age)
        else:
            raise ValueError(f"Diameter class '{diameter_class}' not found for species '{species}'.")
    else:
        raise ValueError(f"Species '{species}' not found in growth rates data.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate the estimated age of a tree based on its species, circumference, and environmental conditions."
    )
    parser.add_argument("species", type=str, help="Species of the tree (e.g., 'Red Spruce', 'Sugar Maple')")
    parser.add_argument("circumference_cm", type=float, help="Circumference of the tree in centimeters")
    parser.add_argument("--winter_temp", type=float, default=-2, help="Average winter temperature in degrees Celsius (default: -2°C)")
    parser.add_argument("--summer_temp", type=float, default=21, help="Average summer temperature in degrees Celsius (default: 21°C)")
    parser.add_argument("--elevation", type=float, default=56, help="Elevation in meters (default: 56m)")
    parser.add_argument("--soil_type", type=str, default="loamy", choices=["loamy", "sandy", "rocky"],
                        help="Soil type around the tree (default: loamy)")
    parser.add_argument("--tree_age", type=int, default=None,
                        help="Known or estimated age of the tree, if applicable (affects growth rate adjustment)")

    args = parser.parse_args()

    try:
        age = calculate_tree_age(
            args.species, args.circumference_cm, args.winter_temp,
            args.summer_temp, args.elevation, args.tree_age, args.soil_type
        )
        print(f"The estimated age of the {args.species} tree is approximately {age} years.")
    except ValueError as e:
        print(e)
