# ETo Estimation Tool (FAO-56 Method)

This Python script calculates **Reference Evapotranspiration (ETo)** using the FAO Penman-Monteith method. This tool includes a graphical user interface (GUI) and is designed for ease of use by agronomists, researchers, and students. The GUI allows intuitive input and generates an Excel file with all intermediate calculations and final ETo values.

---

## Features

- User-friendly GUI built with Tkinter
- Required climate data: Tmax, Tmin, dew point temperature, and wind velocity (no radiation data required)
- Climate data import from '.xlsx' file
- Automatic unit conversion:
  - Temperature: °F or °C
  - Wind speed: knots or m/s
- Intermediate calculations:
  - VPD: vapour pressure deficit (kPa)
  - Δ: Slope of saturation vapour pressure curve (kPa/°C)
  - dr: inverse relative distance Earth-Sun
  - δ: solar declination (radians)
  - ws: sunset hour angle (radians)
  - Ra: extraterrestrial radiation (MJ/m2/day)
  - Rs: solar or shortwave radiation (MJ/m2/day)
  - Rns: net solar or shortwave radiation (MJ/m2/day)
  - Rso: clear-sky solar radiation (MJ/me2/day)
  - Rnl: net longwave radiation (MJ/m2/day)
  - Rn: net radiation (MJ/m2/day)
- Radiation parameters calculated based on:
  - Julian day
  - Latitude
  - Altitude
  - Geographic zone (interior or coast)
- Final ETo estimation in (mm/day)
- Outputs all results to a well-structured Excel file '.xlsx'

---

## Input 

### 1) Climate data (from Excel file):

- A '.xlsx' file with **4 columns and no headers**:
  1. Maximum temperature (Tmax)
  2. Minimum temperature (Tmin)
  3. Dew point temperature Tdew
  4. Wind speed
     
### 2) Time, Location and Units Parameters (entered via GUI):

  1. Altitude (meters above sea level, msnm)
  2. Units for each parameter
  3. Initial date (date of first row in Excel file)
  4. Latitude (decimal degrees)
  5. Geographic zone: "Interior" or "Coast"

---

## Output

An '.xlsx' file containing:
- Converted input climate data
- Intermediate variables (e.g., VPD, radiation)
- Final ETo values (mm/day)

All values are rounded to 3 decimal places for clarity.

---

## Requirements

- Python 3.9+
- `pandas`
- `numpy`
- `tkinter`
- `tkcalendar`

### Install required packages:

```bash
pip install pandas numpy tkcalendar
