# Bivariate QGIS Scripts

Three QGIS Processing scripts for creating bivariate choropleth maps. Visualize two variables simultaneously using color combinations.

## Scripts

1. **Bivariate_Raster_Generator.py** - Combines two variables into a bivariate raster (3x3 or 4x4 grid)
2. **Bivariate_Style_Generator.py** - Applies color schemes to the bivariate raster
3. **Bivariate_Legend_Box_Generator.py** - Creates a 2D legend for the map

## Installation

**Copy to Scripts Folder:**
- Windows: `C:\Users\[YourUsername]\AppData\Roaming\QGIS\QGIS3\profiles\default\processing\scripts`
- macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts`
- Linux: `~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts`

Then restart QGIS or refresh the Processing Toolbox.

## Usage

1. Open Processing Toolbox (`Ctrl+Alt+T`)
2. Find scripts under **Scripts** section
3. Run in order:
   - Generate bivariate raster from two input layers
   - Apply styling with color scheme
   - Create legend graphic

## Tips

- Use normalized data (rates/percentages, not raw counts)
- Stick to 3x3 or 4x4 classifications
- Ensure all layers use the same CRS
- Choose color schemes with good contrast

## Resources

- [Joshua Stevens - Bivariate Choropleth Maps](https://www.joshuastevens.net/cartography/make-a-bivariate-choropleth-map/)
- [BNHR - Bivariate Choropleths in QGIS](https://bnhr.xyz/2019/09/15/bivariate-choropleths-in-qgis.html)
