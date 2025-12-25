## Bivariate Style Generator (QML Creator & Applier)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer,
    QgsProcessingParameterEnum, QgsProcessingParameterString,
    QgsProcessingParameterFileDestination, QgsProcessingParameterBoolean,
    QgsProcessingException
)
import processing

# ---------- Color Palettes ----------
PALETTE_PURPLE_BLUE = [
    (11, 'Low A, Low B',       '#E8E8E8'),
    (12, 'Low A, Medium B',    '#ADE2E5'),
    (13, 'Low A, High B',      '#5AC8C9'),
    (21, 'Medium A, Low B',    '#DEB0D5'),
    (22, 'Medium A, Medium B', '#A4ADD1'),
    (23, 'Medium A, High B',   '#5399B8'),
    (31, 'High A, Low B',      '#BE64AC'),
    (32, 'High A, Medium B',   '#8C62AA'),
    (33, 'High A, High B',     '#3A4893'),
]

PALETTE_ORANGE_GREEN = [
    (11, 'Low A, Low B',       '#D3D3D3'),
    (12, 'Low A, Medium B',    '#7FBBD2'),
    (13, 'Low A, High B',      '#149ED0'),
    (21, 'Medium A, Low B',    '#D9A386'),
    (22, 'Medium A, Medium B', '#819084'),
    (23, 'Medium A, High B',   '#147884'),
    (31, 'High A, Low B',      '#DE692A'),
    (32, 'High A, Medium B',   '#855E28'),
    (33, 'High A, High B',     '#164E28'),
]

COLOR_PALETTES = {
    'purple_blue': PALETTE_PURPLE_BLUE,
    'orange_green': PALETTE_ORANGE_GREEN,
}

# ---------- QML writer ----------
def write_bivariate_qml(qml_path, palette_key='purple_blue', custom_palette=None):
    """Writes a QGIS paletted raster style (.qml) using a selected color palette or custom colors."""
    # Use custom palette if provided, otherwise use predefined palette
    if custom_palette:
        items = custom_palette
    else:
        items = COLOR_PALETTES.get(palette_key, PALETTE_PURPLE_BLUE)

    doctype = "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
    header = (
        '<qgis autoRefreshTime="0" version="3.22.0-Bialowieza" '
        'styleCategories="LayerConfiguration|Symbology|MapTips|AttributeTable|Rendering|CustomProperties|Temporal|Elevation|Notes" '
        'maxScale="0" autoRefreshMode="Disabled" hasScaleBasedVisibilityFlag="0" minScale="1e+08">\n'
        '  <flags><Identifiable>1</Identifiable><Removable>1</Removable><Searchable>1</Searchable></flags>\n'
        '  <pipe>\n'
        '    <provider><resampling zoomedOutResamplingMethod="nearestNeighbour" enabled="false" '
        'zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2"/></provider>\n'
        '    <rasterrenderer opacity="1" band="1" type="paletted" alphaBand="-1" nodataColor="">\n'
        '      <rasterTransparency/>\n'
        '      <colorPalette>\n'
    )
    body = ''.join(
        f'        <paletteEntry alpha="255" label="{label}" color="{hexcolor}" value="{val}"/>\n'
        for (val, label, hexcolor) in items
    )
    footer = (
        '      </colorPalette>\n'
        '      <colorramp type="randomcolors" name="[source]"/>\n'
        '    </rasterrenderer>\n'
        '    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>\n'
        '    <rasterresampler maxOversampling="2"/>\n'
        '  </pipe>\n'
        '  <blendMode>0</blendMode>\n'
        '</qgis>\n'
    )
    with open(qml_path, 'w', encoding='utf-8') as f:
        f.write(doctype + header + body + footer)
    return qml_path


# ---------- Processing Algorithm ----------
class BivariateStyleGenerator(QgsProcessingAlgorithm):
    # Params
    INPUT_RASTER = 'INPUT_RASTER'
    PALETTE_CHOICE = 'PALETTE_CHOICE'
    CUSTOM_COLORS = 'CUSTOM_COLORS'
    AUTO_APPLY = 'AUTO_APPLY'
    OUT_QML = 'OUT_QML'

    def tr(self, text): 
        return QCoreApplication.translate('BivariateStyleGenerator', text)
    
    def createInstance(self): 
        return BivariateStyleGenerator()
    
    def name(self): 
        return 'bivariate_style_generator'
    
    def displayName(self): 
        return self.tr('Bivariate Style Generator')
    
    def group(self): 
        return self.tr('Raster - Bivariate')
    
    def groupId(self): 
        return 'raster_bivariate'
    
    def shortHelpString(self):
        return self.tr(
            'Creates and optionally applies a color style (QML file) for bivariate raster data (codes 11-33).\n\n'
            'This tool works with rasters that have values from 11 to 33, representing combinations of '
            'three classes (Low/Medium/High) for two variables.\n\n'
            'Choose from predefined color palettes or provide custom colors:\n'
            '- Custom Colors: Enter 9 hex codes separated by commas\n'
            '- Order: 11, 12, 13, 21, 22, 23, 31, 32, 33\n'
            '- Example: #E9E9EB, #A3C6DA, #55A5C7, #ECD088, #A6B37E, #579574, #F5B903, #AEA003, #5D8103\n\n'
            'The tool can automatically apply the style to your input raster layer.'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT_RASTER, 
            self.tr('Input Bivariate Raster (values 11-33)'),
            optional=True))

        self.addParameter(QgsProcessingParameterEnum(
            self.PALETTE_CHOICE,
            self.tr('Color Palette'),
            options=['Blue-Purple', 'Blue-Orange-Green', 'Custom (use hex codes below)'],
            defaultValue=0,
            optional=False
        ))

        self.addParameter(QgsProcessingParameterString(
            self.CUSTOM_COLORS,
            self.tr('Custom Colors (9 hex codes, comma-separated)'),
            defaultValue='#E9E9EB, #A3C6DA, #55A5C7, #ECD088, #A6B37E, #579574, #F5B903, #AEA003, #5D8103',
            optional=True,
            multiLine=False
        ))

        self.addParameter(QgsProcessingParameterBoolean(
            self.AUTO_APPLY,
            self.tr('Automatically apply style to input raster?'),
            defaultValue=True
        ))

        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUT_QML, 
            self.tr('Output QML Style File'), 
            'QML files (*.qml)'))

    def parse_custom_colors(self, color_string, feedback):
        """Parse comma-separated hex color codes and create a palette list."""
        # Clean and split the input
        colors = [c.strip().upper() for c in color_string.split(',')]
        
        # Validate we have exactly 9 colors
        if len(colors) != 9:
            raise QgsProcessingException(
                f'Expected 9 hex codes, but got {len(colors)}. '
                'Please provide exactly 9 colors separated by commas.'
            )
        
        # Validate hex format
        for i, color in enumerate(colors):
            if not color.startswith('#'):
                color = '#' + color
                colors[i] = color
            
            if len(color) != 7:
                raise QgsProcessingException(
                    f'Invalid hex code: {color}. '
                    'Each color must be in format #RRGGBB (e.g., #E9E9EB)'
                )
            
            # Validate hex characters
            try:
                int(color[1:], 16)
            except ValueError:
                raise QgsProcessingException(
                    f'Invalid hex code: {color}. '
                    'Use only valid hexadecimal characters (0-9, A-F)'
                )
        
        # Map colors to bivariate codes (11-33)
        codes = [11, 12, 13, 21, 22, 23, 31, 32, 33]
        a_levels = ['Low', 'Medium', 'High']
        b_levels = ['Low', 'Medium', 'High']
        
        palette = []
        for i, code in enumerate(codes):
            a_idx = (code // 10) - 1  # Get A level (1-3 -> 0-2)
            b_idx = (code % 10) - 1   # Get B level (1-3 -> 0-2)
            label = f'{a_levels[a_idx]} A, {b_levels[b_idx]} B'
            palette.append((code, label, colors[i]))
            feedback.pushInfo(f'Code {code}: {colors[i]} - {label}')
        
        return palette

    def processAlgorithm(self, parameters, context, feedback):
        try:
            input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
            palette_index = self.parameterAsInt(parameters, self.PALETTE_CHOICE, context)
            custom_colors = self.parameterAsString(parameters, self.CUSTOM_COLORS, context)
            auto_apply = self.parameterAsBoolean(parameters, self.AUTO_APPLY, context)
            out_qml = self.parameterAsFileOutput(parameters, self.OUT_QML, context)

            # Validate input raster if auto-apply is enabled
            if auto_apply and (not input_raster or not input_raster.isValid()):
                raise QgsProcessingException(
                    "Input raster is required when 'Auto-apply style' is enabled. "
                    "Please select a valid raster layer or disable auto-apply."
                )

            # Determine which palette to use
            custom_palette = None
            selected_palette_key = None
            
            if palette_index == 2:  # Custom colors
                feedback.pushInfo('Using custom color palette...')
                if not custom_colors or custom_colors.strip() == '':
                    raise QgsProcessingException(
                        'Custom colors option selected but no colors provided. '
                        'Please enter 9 hex codes separated by commas.'
                    )
                custom_palette = self.parse_custom_colors(custom_colors, feedback)
            else:  # Predefined palettes
                palette_keys = ['purple_blue', 'orange_green']
                selected_palette_key = palette_keys[palette_index]
                feedback.pushInfo(f'Using {selected_palette_key} palette')

            # Write QML file
            feedback.pushInfo("Writing QML style file...")
            style_written = write_bivariate_qml(out_qml, selected_palette_key, custom_palette)
            feedback.pushInfo(f"QML file created: {style_written}")

            # Apply style if requested
            if auto_apply and input_raster:
                try:
                    feedback.pushInfo("Applying style to input raster...")
                    processing.run('qgis:setstyleforrasterlayer', 
                                   {'INPUT': input_raster, 'STYLE': style_written},
                                   context=context, feedback=feedback)
                    feedback.pushInfo("Style applied successfully!")
                except Exception as e:
                    feedback.pushWarning(f"Could not auto-apply style: {str(e)}")
                    feedback.pushWarning("You can manually apply the QML file to your raster layer.")
            
            feedback.pushInfo('='*50)
            feedback.pushInfo('Style generation complete!')
            if not auto_apply:
                feedback.pushInfo('To apply the style: Right-click your raster layer > Properties > Symbology > Style > Load Style')
            
            return {self.OUT_QML: style_written}
            
        except Exception as e:
            feedback.reportError(f"Error: {str(e)}", True)
            raise QgsProcessingException(str(e))

def classFactory(iface=None):
    return BivariateStyleGenerator()
