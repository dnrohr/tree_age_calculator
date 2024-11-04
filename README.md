# Tree Age Estimator

This Python program calculates the estimated age of a tree based on its species, circumference, and environmental factors such as temperature, elevation, and soil type. The program uses data and insights derived from the research paper:

> **"Regionally Averaged Diameter Growth in New England Forests"**  
> by Robert B. Smith, James W. Hornbeck, C. Anthony Federer, and Paul J. Krusic, Jr.  
> Published by the USDA Forest Service, Northeastern Forest Experiment Station (Research Paper NE-637)

This program adjusts the basal area increment (BAI) growth rates based on conditions specific to New England tree species, including Red Spruce, Sugar Maple, and others, as detailed in the research paper.

## Features
- Calculates tree age based on species-specific basal area increments (BAI).
- Adjusts growth rate based on:
  - **Seasonal Temperatures**: Winter and summer temperature adjustments.
  - **Elevation**: Higher elevations have reduced growth rates.
  - **Soil Type**: Different soil types (e.g., sandy, rocky) affect growth.
  - **Tree Age**: Maturation effects can slow growth in older trees.

## Requirements
- Python 3.x

## Installation
Clone this repository and navigate to the directory where the `tree_age_calculator.py` file is located.

```bash
git clone <repository-url>
cd <repository-directory>
```

## Usage
The program can be run from the command line with required and optional arguments.

### Required Arguments
1. `species` - The species of the tree (e.g., `"Red Spruce"`).
2. `circumference_cm` - The circumference of the tree in centimeters.

### Optional Arguments
- `--winter_temp` - Average winter temperature in degrees Celsius (default: -2°C).
- `--summer_temp` - Average summer temperature in degrees Celsius (default: 21°C).
- `--elevation` - Elevation in meters (default: 56m).
- `--soil_type` - Soil type around the tree (`loamy`, `sandy`, or `rocky`; default: `loamy`).
- `--tree_age` - Known or estimated age of the tree (if available), affecting growth rate adjustment.

### Example Commands
To calculate tree age with default environmental factors:
```bash
python tree_age_calculator.py "Red Spruce" 100
```

To specify environmental factors explicitly:
```bash
python tree_age_calculator.py "Red Spruce" 100 --winter_temp -5 --summer_temp 18 --elevation 700 --soil_type sandy --tree_age 60
```

### Help Command
To view help and usage information:
```bash
python tree_age_calculator.py --help
```

## Example Output
```text
The estimated age of the Red Spruce tree is approximately 85 years.
```

## How the Program Works
1. **Input Parsing**: The program uses `argparse` to parse input arguments.
2. **Growth Rate Calculation**: It assigns a basal area increment (BAI) growth rate based on species and diameter class (small, medium, large).
3. **Environmental Adjustments**: Adjusts growth rate based on:
   - **Temperature**: Warmer winters and cooler summers tend to increase growth, while extreme cold or heat may reduce it.
   - **Elevation**: Higher elevations introduce more environmental stress, reducing growth.
   - **Soil Type**: Loamy soil is ideal for growth, while sandy or rocky soils slightly reduce it.
4. **Age Calculation**: Calculates tree age using the adjusted growth rate to provide an estimate.

## References
Smith, R. B., Hornbeck, J. W., Federer, C. A., & Krusic, P. J. (1990). *Regionally Averaged Diameter Growth in New England Forests*. USDA Forest Service, Northeastern Forest Experiment Station. Research Paper NE-637.
