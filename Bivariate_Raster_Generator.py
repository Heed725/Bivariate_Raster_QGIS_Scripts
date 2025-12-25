## Bivariate Raster Generator (Quantile-based Classification)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer,
    QgsProcessingParameterBoolean, QgsProcessingParameterCrs,
    QgsProcessingParameterNumber, QgsProcessingParameterRasterDestination,
    QgsRasterLayer, QgsProcessingException
)
import processing
from osgeo import gdal
import numpy as np
import os, tempfile

# ---------- Raster calculator helpers ----------
def _calc_gdal(expr, layer_A, layer_B, out_path, rtype=6):
    """GDAL raster calculator using variables A,B. Using Float32 (rtype=6) for better compatibility."""
    params = {
        'INPUT_A': layer_A, 'BAND_A': 1, 
        'INPUT_B': layer_B, 'BAND_B': 1,
        'FORMULA': expr, 
        'NO_DATA': None, 
        'RTYPE': rtype, 
        'OPTIONS': '',
        'EXTRA': '',
        'OUTPUT': out_path
    }
    return processing.run('gdal:rastercalculator', params)

def _calc_qgis(expr, layers, out_path):
    """QGIS raster calculator using layer references."""
    from qgis.core import QgsProcessingContext
    
    entries = []
    layer_dict = {}
    
    for idx, layer_path in enumerate(layers):
        ref_name = chr(65 + idx)  # A, B, C, etc.
        if isinstance(layer_path, str):
            layer = QgsRasterLayer(layer_path, f'layer_{ref_name}')
        else:
            layer = layer_path
            
        if not layer.isValid():
            raise QgsProcessingException(f"Invalid layer: {layer_path}")
            
        from qgis.analysis import QgsRasterCalculatorEntry
        entry = QgsRasterCalculatorEntry()
        entry.ref = f'{ref_name}@1'
        entry.raster = layer
        entry.bandNumber = 1
        entries.append(entry)
        layer_dict[ref_name] = layer
    
    from qgis.analysis import QgsRasterCalculator
    calc = QgsRasterCalculator(
        expr,
        out_path,
        'GTiff',
        layer_dict['A'].extent(),
        layer_dict['A'].width(),
        layer_dict['A'].height(),
        entries
    )
    
    result = calc.processCalculation()
    if result != 0:
        raise QgsProcessingException(f"Raster calculation failed with code: {result}")
    
    return {'OUTPUT': out_path}

def _runcalc_dual(qgis_expr, gdal_expr, layers, out_path, feedback):
    """Try GDAL calc first (more reliable); fall back to QGIS calc."""
    A = layers[0]
    B = layers[1] if len(layers) > 1 else layers[0]
    
    try:
        feedback.pushInfo(f"Attempting GDAL calculation: {gdal_expr}")
        return _calc_gdal(gdal_expr, A, B, out_path)
    except Exception as e_gdal:
        feedback.pushWarning(f"GDAL calculator failed: {str(e_gdal)}")
        try:
            feedback.pushInfo(f"Attempting QGIS calculation: {qgis_expr}")
            return _calc_qgis(qgis_expr, layers, out_path)
        except Exception as e_qgis:
            raise QgsProcessingException(
                f"Raster calculator failed in both GDAL and QGIS.\n"
                f"GDAL error: {e_gdal}\nQGIS error: {e_qgis}"
            )


# ---------- Processing Algorithm ----------
class BivariateRasterGenerator(QgsProcessingAlgorithm):
    # Params
    RASTER_A, RASTER_B = 'RASTER_A', 'RASTER_B'
    TARGET_CRS, DO_REPROJECT_ALIGN = 'TARGET_CRS', 'DO_REPROJECT_ALIGN'
    APPLY_DIVISOR_B, DIVISOR_B = 'APPLY_DIVISOR_B', 'DIVISOR_B'
    OUT_A_CLASS, OUT_B_CLASS, OUT_BIVAR = 'OUT_A_CLASS', 'OUT_B_CLASS', 'OUT_BIVAR'

    def tr(self, text): 
        return QCoreApplication.translate('BivariateRasterGenerator', text)
    
    def createInstance(self): 
        return BivariateRasterGenerator()
    
    def name(self): 
        return 'bivariate_raster_generator'
    
    def displayName(self): 
        return self.tr('Bivariate Raster Generator')
    
    def group(self): 
        return self.tr('Raster - Bivariate')
    
    def groupId(self): 
        return 'raster_bivariate'
    
    def shortHelpString(self):
        return self.tr(
            'Generates 3-quantile classes (1/2/3) for two rasters and combines them into bivariate codes 11-33.\n\n'
            'This tool performs the raster processing only. Use the "Bivariate Style Generator" tool to create '
            'and apply color styles to the output.\n\n'
            'Options:\n'
            '- Optionally aligns grids to match Raster A\n'
            '- Optionally divides Raster B by a factor (useful for unit conversion)\n'
            '- Outputs: Individual class rasters (1-3) and combined bivariate raster (11-33)'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.RASTER_A, self.tr('Raster A (e.g. Temperature)')))
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.RASTER_B, self.tr('Raster B (e.g. Precipitation)')))

        self.addParameter(QgsProcessingParameterBoolean(
            self.DO_REPROJECT_ALIGN, self.tr('Reproject & align to Raster A grid?'), defaultValue=True))

        self.addParameter(QgsProcessingParameterCrs(
            self.TARGET_CRS, self.tr('Target CRS (optional, e.g. EPSG:21037)'), optional=True))

        self.addParameter(QgsProcessingParameterBoolean(
            self.APPLY_DIVISOR_B, self.tr('Divide Raster B by factor before processing?'),
            defaultValue=False))
        self.addParameter(QgsProcessingParameterNumber(
            self.DIVISOR_B, self.tr('Division factor for Raster B (e.g. 30)'),
            type=QgsProcessingParameterNumber.Double, defaultValue=30.0, minValue=1e-6))

        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUT_A_CLASS, self.tr('Output: Raster A class (1-3)')))
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUT_B_CLASS, self.tr('Output: Raster B class (1-3)')))
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUT_BIVAR, self.tr('Output: Bivariate code (11-33)')))

    def processAlgorithm(self, parameters, context, feedback):
        try:
            raster_a = self.parameterAsRasterLayer(parameters, self.RASTER_A, context)
            raster_b = self.parameterAsRasterLayer(parameters, self.RASTER_B, context)
            
            if not raster_a or not raster_a.isValid():
                raise QgsProcessingException("Raster A is invalid")
            if not raster_b or not raster_b.isValid():
                raise QgsProcessingException("Raster B is invalid")
            
            do_align = self.parameterAsBoolean(parameters, self.DO_REPROJECT_ALIGN, context)
            target_crs = self.parameterAsCrs(parameters, self.TARGET_CRS, context)
            apply_div_b = self.parameterAsBoolean(parameters, self.APPLY_DIVISOR_B, context)
            divisor_b = self.parameterAsDouble(parameters, self.DIVISOR_B, context)

            out_a_class = self.parameterAsOutputLayer(parameters, self.OUT_A_CLASS, context)
            out_b_class = self.parameterAsOutputLayer(parameters, self.OUT_B_CLASS, context)
            out_bivar = self.parameterAsOutputLayer(parameters, self.OUT_BIVAR, context)

            tmpdir = tempfile.mkdtemp(prefix='bivar_')
            feedback.pushInfo(f"Working directory: {tmpdir}")

            # ---------- Reproject & Align ----------
            def warp_to_match(src, dst, ref, t_srs, feedback):
                feedback.pushInfo(f"Warping {os.path.basename(src)} to match reference")
                ref_ds = gdal.Open(ref)
                if ref_ds is None:
                    raise QgsProcessingException(f"Cannot open reference raster: {ref}")
                
                gt = ref_ds.GetGeoTransform()
                px, py = abs(gt[1]), abs(gt[5])
                minx, maxy = gt[0], gt[3]
                cols, rows = ref_ds.RasterXSize, ref_ds.RasterYSize
                maxx, miny = minx + cols * px, maxy - rows * py
                
                target_extent_str = f"{minx},{maxx},{miny},{maxy}"
                
                args = {
                    'INPUT': src,
                    'SOURCE_CRS': None,
                    'TARGET_CRS': t_srs,
                    'RESAMPLING': 1,  # Bilinear
                    'NODATA': None,
                    'TARGET_EXTENT': target_extent_str,
                    'TARGET_EXTENT_CRS': t_srs,
                    'TARGET_RESOLUTION': px,
                    'OPTIONS': '',
                    'DATA_TYPE': 6,  # Float32
                    'MULTITHREADING': True,
                    'OUTPUT': dst
                }
                
                result = processing.run('gdal:warpreproject', args, context=context, feedback=feedback)
                ref_ds = None
                return result

            path_a = raster_a.source()
            path_b = raster_b.source()
            final_crs = target_crs if target_crs.isValid() else raster_a.crs()

            if do_align:
                feedback.pushInfo("Aligning rasters...")
                a_ref = os.path.join(tmpdir, 'A_ref.tif')
                warp_to_match(path_a, a_ref, path_a, final_crs, feedback)
                
                a_al = os.path.join(tmpdir, 'A_aligned.tif')
                warp_to_match(a_ref, a_al, a_ref, final_crs, feedback)
                
                b_al = os.path.join(tmpdir, 'B_aligned.tif')
                warp_to_match(path_b, b_al, a_al, final_crs, feedback)
            else:
                a_al, b_al = path_a, path_b

            # ---------- Optional divide Raster B ----------
            b_input = b_al
            if apply_div_b:
                feedback.pushInfo(f"Dividing Raster B by {divisor_b}")
                b_scaled = os.path.join(tmpdir, 'B_scaled.tif')
                _runcalc_dual(f'"B@1"/{divisor_b}', f'B/{divisor_b}', [b_al], b_scaled, feedback)
                b_input = b_scaled

            # ---------- Compute quantiles (terciles) ----------
            def quantiles(path, feedback):
                feedback.pushInfo(f"Computing quantiles for {os.path.basename(path)}")
                ds = gdal.Open(path)
                if ds is None:
                    raise QgsProcessingException(f"Cannot open raster: {path}")
                
                band = ds.GetRasterBand(1)
                arr = band.ReadAsArray().astype('float64')
                nd = band.GetNoDataValue()
                
                if nd is not None:
                    arr[arr == nd] = np.nan
                
                vals = arr[~np.isnan(arr)]
                ds = None
                
                if vals.size == 0:
                    raise QgsProcessingException("No valid pixels to compute quantiles")
                
                q1, q2 = np.percentile(vals, [33.333, 66.667])
                feedback.pushInfo(f"  Q1: {q1:.4f}, Q2: {q2:.4f}")
                return q1, q2

            a_q1, a_q2 = quantiles(a_al, feedback)
            b_q1, b_q2 = quantiles(b_input, feedback)

            # ---------- Reclassify to 1/2/3 ----------
            feedback.pushInfo("Reclassifying Raster A...")
            qgis_expr_A = f'("A@1"<={a_q1})*1 + (("A@1">{a_q1}) * ("A@1"<={a_q2}))*2 + ("A@1">{a_q2})*3'
            gdal_expr_A = f'(A<={a_q1})*1 + ((A>{a_q1})*(A<={a_q2}))*2 + (A>{a_q2})*3'
            _runcalc_dual(qgis_expr_A, gdal_expr_A, [a_al], out_a_class, feedback)

            feedback.pushInfo("Reclassifying Raster B...")
            qgis_expr_B = f'("B@1"<={b_q1})*1 + (("B@1">{b_q1}) * ("B@1"<={b_q2}))*2 + ("B@1">{b_q2})*3'
            gdal_expr_B = f'(B<={b_q1})*1 + ((B>{b_q1})*(B<={b_q2}))*2 + (B>{b_q2})*3'
            _runcalc_dual(qgis_expr_B, gdal_expr_B, [b_input], out_b_class, feedback)

            # ---------- Combine into 11..33 ----------
            feedback.pushInfo("Combining into bivariate classes...")
            _runcalc_dual('"A@1"*10+"B@1"', '(A*10)+B', [out_a_class, out_b_class], out_bivar, feedback)

            feedback.pushInfo('='*50)
            feedback.pushInfo(f'Raster A Terciles: q1={a_q1:.4f}, q2={a_q2:.4f}')
            feedback.pushInfo(f'Raster B Terciles: q1={b_q1:.4f}, q2={b_q2:.4f}')
            feedback.pushInfo('='*50)
            feedback.pushInfo('Bivariate raster generated successfully!')
            feedback.pushInfo('Use "Bivariate Style Generator" to apply colors.')

            results = {
                self.OUT_A_CLASS: out_a_class,
                self.OUT_B_CLASS: out_b_class,
                self.OUT_BIVAR: out_bivar
            }
            
            return results
            
        except Exception as e:
            feedback.reportError(f"Error: {str(e)}", True)
            raise QgsProcessingException(str(e))

def classFactory(iface=None):
    return BivariateRasterGenerator()
