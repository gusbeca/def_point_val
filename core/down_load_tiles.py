# -*- coding: utf-8 -*-
import subprocess

import requests
from requests.auth import HTTPBasicAuth


try:
    from pygeotile.tile import Tile
except:
    subprocess.check_call(['python3', '-m', 'pip', 'install', 'pyGeoTile'])

from qgis.PyQt.QtCore import QVariant
from qgis.core import *
import os.path

def chipTiles(p,z):
    """
    find Planet Tile for a give point p at given zool level z
    :param p: (lat, long)
    :param z: 15
    :return: x,y,z tile google xyz tile grid
    """
    latitude, longitude, zoom = p[0],p[1], z
    tile = Tile.for_latitude_longitude(latitude, longitude, zoom)
    tile = tile.google
    return tile

def setTiles(self):
    """
    find google tiles for every point and add atribute to vectorfile
    :param self:
    :return:
    """
    features = self.inVector.getFeatures()
    self.inVector.startEditing()
    if self.inVector.dataProvider().fieldNameIndex("tile_B") == -1:
        self.inVector.dataProvider().addAttributes([QgsField("tile_B", QVariant.String)])
        self.inVector.dataProvider().addAttributes([QgsField("tile_A", QVariant.String)])
        self.inVector.dataProvider().addAttributes([QgsField("tile_x", QVariant.String)])
        self.inVector.dataProvider().addAttributes([QgsField("tile_y", QVariant.String)])

        self.inVector.updateFields()

    id_new_col_B = self.inVector.dataProvider().fieldNameIndex("tile_B")
    id_new_col_A = self.inVector.dataProvider().fieldNameIndex("tile_A")
    id_new_col_x = self.inVector.dataProvider().fieldNameIndex("tile_x")
    id_new_col_y = self.inVector.dataProvider().fieldNameIndex("tile_y")

    for feature in features:
        geom = feature.geometry()
        centroid = geom.centroid()
        longitude = centroid.asPoint().x()
        latitude = centroid.asPoint().y()
        p = [latitude, longitude]
        ptile = chipTiles(p, 15)
        tile_b = self.mosaicNameBefore + "_15_" + str(ptile[0]) + "_" + str(ptile[1])
        tile_a = self.mosaicNameAfter + "_15_" + str(ptile[0]) + "_" + str(ptile[1])
        self.inVector.changeAttributeValue(feature.id(), id_new_col_B, tile_b)
        self.inVector.changeAttributeValue(feature.id(), id_new_col_A, tile_a)
        self.inVector.changeAttributeValue(feature.id(), id_new_col_x, str(ptile[0]))
        self.inVector.changeAttributeValue(feature.id(), id_new_col_y, str(ptile[1]))

    self.inVector.commitChanges()


def getTile(self):
    """
    download tile from planet
    :param self:
    :return:
    """
    if not os.path.exists(self.outRaster):
        os.mkdir(self.outRaster)
    features = self.inVector.getFeatures()
    self.inVector.startEditing()
    if self.inVector.dataProvider().fieldNameIndex("bounds") == -1:
        self.inVector.dataProvider().addAttributes([QgsField("bounds", QVariant.String)])
    self.inVector.updateFields()

    id_new_col_bounds = self.inVector.dataProvider().fieldNameIndex("bounds")

    for feature in features:
        x = int(feature['tile_x'])
        y = int(feature['tile_y'])
        google_x, google_y, zoom = x, y, 15
        tile = Tile.from_google(google_x, google_y, zoom)
        self.inVector.changeAttributeValue(feature.id(), id_new_col_bounds, str(tile.bounds))

        fileNameB = feature['tile_B']+".png"
        fileNameA = feature['tile_A']+".png"
        if not os.path.exists(self.outRaster + '/' + fileNameB):  # Si no existe la imagen se descarga
            result = requests.get(
                'https://tiles.planet.com/basemaps/v1/planet-tiles/%s/gmap/%s/%s/%s.png' % (self.mosaicNameBefore, str(15), x, y),
                auth=HTTPBasicAuth(os.environ['PL_API_KEY_IDEAM'], ''))

            with open(self.outRaster+ '/' + fileNameB, 'wb') as f:
                f.write(result.content)  # Guardar imagen en archivo


        if not os.path.exists(self.outRaster + '/' + fileNameA):  # Si no existe la imagen se descarga
            result = requests.get(
                'https://tiles.planet.com/basemaps/v1/planet-tiles/%s/gmap/%s/%s/%s.png' % (
                self.mosaicNameAfter, str(15), x, y),
                auth=HTTPBasicAuth(os.environ['PL_API_KEY_IDEAM'], ''))

            with open(self.outRaster + '/' + fileNameA, 'wb') as f:
                f.write(result.content)  # Guardar imagen en archivo

    self.inVector.commitChanges()
