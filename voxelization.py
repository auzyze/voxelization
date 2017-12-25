# -*- coding: utf-8 -*-
"""
Functions that can voxelization the *.ply files
python 2.7
Author: Chaoqun Jiang
Home Page: http://mcoder.cc
"""

import pyassimp
import numpy as np
import operator

def voxelization(filename,
    outputJsonPath = '../voxel_json/',
    outputNumpyPath = '../voxel_numpy/',
    size = (192,192,200)):
    """ function voxelization
        This function load a *.ply model file, and convert it into a voxel.
        And export in two formats.

        numpy formats: just use numpy import, a array has shape (192, 192, 200)
        json format: a numpy format reshape to (-1,) and attribute name is 'array'
    Args:
        filename:   a relative file path to the *.ply file
        outputJsonPath: a relative floder path to save voxel in json format
        outputNumpyPath: a relative floder path to save voxel in numpy format
        size: a tuple with 3 integer, default is (192, 192, 200)
    """
    if len(size) != 3:
        print("The argument \" size \" should has three integer")
        return

    scene = pyassimp.load(filename)     # import scene
    meshes_count = len(scene.meshes)    # the count of meshes
    if meshes_count < 1:
        print("Error! The model file has no meshes in it")
        return

    voxel_width = size[0]
    voxel_height = size[1]
    voxel_length = size[2]

    voxel = np.zeros( shape = (voxel_width, voxel_height, voxel_length),
        dtype = np.float32)         # Creat a zeros ndarray

    boundingbox = _getBoundingBox(scene)    # get the bounding box of scene

    # calculate each voxel's edge length
    center = np.array( [ (boundingbox[0] + boundingbox[3]) / 2,
                        (boundingbox[1] + boundingbox[4]) / 2,
                        (boundingbox[2] + boundingbox[5]) /2] )

    x_edge = (boundingbox[0] - boundingbox[3]) / voxel_width
    y_edge = (boundingbox[1] - boundingbox[4]) / voxel_height
    z_edge = (boundingbox[2] - boundingbox[5]) / voxel_length
    edge = max(x_edge, y_edge, z_edge)      # use the max as edge
    print ("x_edge: ", x_edge, "\ny_edge: ", y_edge,
        "\nz_edge: ", z_edge, "\nedge: ", edge)

    # set the (voxel_width // 2, voxel_height // 2, voxel_length // 2)'s
    # position is center. So we can get other voxel box's voxel box.
    # At here, we calculate the start voxel box's center position.
    start = center - np.array([voxel_width // 2 * edge,
        voxel_height // 2 * edge, voxel_length // 2 * edge])


def _getBoundingBox(scene):
    """give a assimp scene, get it bounding box
            It will bounding all meshes in the mesh.
        Args:
            scene: assimp scene
        Returns:
            bounding box ( xmax, ymax, zmax, xmin, ymin, zmin )
            6 num represent 6 faces.
    """
    if len(scene.meshes) == 0:
        print("scene's meshes attribute has no mesh")
        return (0,0,0,0,0,0)

    mesh_1 = scene.meshes[0]
    xmax, ymax, zmax = np.amax( mesh_1.vertices, axis = 0 )
    xmin, ymin, zmin = np.amin( mesh_1.vertices, axis = 0 )

    for index in range(1,len(scene.meshes)):
        mesh_t = scene.meshes[index]
        xmax_t, ymax_t, zmax_t = np.amax( mesh_t.vertices, axis = 0)
        xmin_t, ymin_t, zmin_t = np.amin( mesh_t.vertices, axis = 0)

        if xmax_t > xmax:   xmax = xmax_t
        if ymax_t > ymax:   ymax = ymax_t
        if zmax_t > zmax:   zmax = zmax_t
        if xmin_t < xmin:   xmin = xmin_t
        if ymin_t < ymin:   ymin = ymin_t
        if zmin_t < zmin:   zmin = zmin_t

    return (xmax, ymax, zmax, xmin, ymin, zmin)

def _meshVoxel(startpoint, edge, mesh, voxel):
    """ mesh voxel function
    change numpy.ndarray's 0 to 1 acounding to mesh and scene'bounding box
    Args:
        startpoint: numpy.ndarray with shape of (3,)
        mesh: pyassimp mesh
        voxel: numpy.ndarray
    """
    vertices = mesh.vertices    #  np.array n x 3
    flann = pyflann.FLANN()     # create a FLANN object
