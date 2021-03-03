import os,sys
import glob
import fnmatch
import zipfile
import shutil
from osgeo import gdal
from osgeo import osr
from osgeo import ogr
from osgeo.gdalconst import *

driver = gdal.GetDriverByName('GTiff')
def unzipScene(zfile,ym,drd,fhcsv):
	tmpdirname = '/tmp'
	if not os.path.exists(tmpdirname):
		os.makedirs(tmpdirname)
	tifdirname = os.path.dirname(zfile).replace('Level-2','TIFF')
	if not os.path.exists(tifdirname):
		os.makedirs(tifdirname)

# Check if file is not corrupt
	corrupt = False
	try:
		archive = zipfile.ZipFile(zfile, 'r')
		try:
			corrupt = True if archive.testzip() else False
		except :
			corrupt = True
			archive.close()
	except zipfile.BadZipfile:
		corrupt = True
	if corrupt:
		fhcsv.write('{},{},{},corrupt\n'.format(ym,drd,zfile))
		print('{} is corrupt'.format(zfile))
		return False
	else:
		archive.extractall(tmpdirname)
		archive.close()

# Get the name of unzipped file in temp directory and transform it into a internally zipped file in TIFF directory
	tiffile = os.path.basename(zfile).replace('.zip','')
	src_filename = os.path.join(tmpdirname,tiffile)
	xmlfile = src_filename.replace('.tif','.xml')
	if os.path.exists(src_filename):
		tifsize = os.path.getsize(src_filename)
		if tifsize < 1000000:
			fhcsv.write('{},{},{},too small\n'.format(ym,drd,zfile))
			print('{} is too small'.format(zfile))
			if os.path.exists(xmlfile):
				os.remove(xmlfile)
				os.remove(src_filename)
			return False
	else:
		fhcsv.write('{},{},{},not exists\n'.format(ym,drd,src_filename))
		print('{} not exists'.format(src_filename))
		if os.path.exists(xmlfile):
			os.remove(xmlfile)
		return False
	dst_filename = os.path.join(tifdirname,tiffile)
	try:
		src_ds = gdal.Open(src_filename)
		dst_ds = driver.CreateCopy(dst_filename, src_ds, options=["COMPRESS=LZW"])
		dst_ds = None
		src_ds = None
		os.remove(src_filename)
	except Exception as e:
		fhcsv.write('{},{},{},{}\n'.format(ym,drd,zfile,gdal.GetLastErrorMsg()))
		if os.path.exists(xmlfile):
			os.remove(xmlfile)
		os.remove(src_filename)
		print('unzipScene - GetLastErrorMsg - {}'.format(gdal.GetLastErrorMsg()))
		return False
# Copy the xml file from tmp to final directory
	if os.path.exists(xmlfile):
		shutil.copy2(xmlfile,tifdirname)
		os.remove(xmlfile)
	return True


sat = sys.argv[1]
dym = '*'
if len(sys.argv) == 3:
	dym = sys.argv[2]
zipdir = '/Level-2/'+sat

csvfile = '{}_{}.csv'.format(sat,dym.replace('*','a'))
fhcsv = open(csvfile, 'w')
fhcsv.write('Date,DRD,File,Status\n')

fzym = sorted(glob.glob('{}/{}'.format(zipdir,dym)))

for zym in fzym:
	ym = os.path.basename(zym)
	zdrds = sorted(glob.glob('{}/*'.format(zym)))
	tym =zym.replace('Level-2','TIFF')
	tdrds = sorted(glob.glob('{}/*'.format(tym)))
	if len(zdrds) == 0:
		print('\n\t',zym,'empty')
		continue
	if len(tdrds) == 0:
		print('\n\t',zym,'not done')
	print(zym,len(zdrds),len(tdrds))

	template =  "*.tif.zip"
	for zdrd in zdrds:
		drd = os.path.basename(zdrd)
		print('Doing',drd)
		zipfiles = [os.path.join(dirpath, f)
			for dirpath, dirnames, files in os.walk("{0}".format(zdrd))
			for f in fnmatch.filter(files, template)]
		if len(zipfiles) == 0:
			print('\t',zdrd,'No zip files')
			continue
		for zipfilename in zipfiles:
			tiffile = zipfilename.replace('Level-2','TIFF').replace('.zip','')
			if os.path.exists(tiffile):
				continue
			status = unzipScene(zipfilename,ym,drd,fhcsv)
fhcsv.close()

	
