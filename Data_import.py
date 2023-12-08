#region imports and settings
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
import tensorflow as tf
import xml.etree.ElementTree as ET

import sklearn
from sklearn.model_selection import KFold, train_test_split

from Models import *

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
#endregion


#region reading initial main dataframe
#Set working directory to the dataset folder
os.chdir(os.path.join(os.getcwd(),'Dataset_FracAtlas'))
#Einlesen der dataset.csv Datei
general_info_df = pd.read_csv('dataset.csv')
#cwd zurück zu ProgrammingDigitalProjects setzen
os.chdir(os.path.join(os.getcwd(),'..'))
#endregion

def showimage(name):
    """
    Shows images using matplotlib package. Args[name: 'image_id.jpg']
    """

    #Navigiert path in Bilder Ordner
    os.chdir(os.path.join(os.getcwd(),'Dataset_FracAtlas','images','all'))
    

    #Plots erstellen, Laden  des Bildes
    fig,ax = plt.subplots()
    ax.imshow(mpimg.imread(name),cmap='gray')

    #cwd zurück auf Standard-Ordner setzen
    os.chdir(os.path.join(os.getcwd(),'..','..','..'))
    
    #Falls Bruch, wird boundingbox auf plot gelegt
    if general_info_df.loc[general_info_df['image_id'] == name, 'fractured'].values == 1:
        rectangle = boundingbox(name,fig,ax)
        ax.add_patch(rectangle)

    #zeigt PLot an
    plt.show()
    
def boundingbox(name,fig,ax):
    #Pathing in xml Ordner
    path = os.path.join(os.getcwd(),'Dataset_FracAtlas','Annotations','PASCAL VOC')
    os.chdir(path)

    #Tree initialisieren
    tree = ET.parse(name[:-3]+'xml')
    root = tree.getroot()

    #Pathing zurück auf Standard-Ordner
    os.chdir(os.path.join(os.getcwd(),'..','..','..'))
    
    #Werte aus bndbox element aus XML ziehen
    values = []
    for x in root[5][4]:
        values.append(int(x.text))
    
    #reassign value 2 und 3, da wir width & height brauchen statt 4 koordinaten für patches.rectangle
    values[2] = values[2]-values[0]
    values[3] = values[3]-values[1]

    #Rechteck wird festgelegt
    bounding_box = patches.Rectangle([values[0],values[1]],width=values[2],height=values[3],linewidth=1,edgecolor='r',facecolor='none')
    
    return bounding_box


def preprocessing(df):
    """
    Creating csv with Columns ['image_id','fractured'] for dataset input pipeline. Args[df: main dataframe]
    """
    #df = df[df['leg'] == 1]
    #inital main dataframe turned into dataset with columns 'image_id' and str('fractured')
    dataset = df[['image_id', 'fractured']].assign(fractured=df['fractured'].astype(str))
    dataset = dataset.sample(frac = 1)

    #Datensatz aufgeteilt in 10% Testdaten und 90% Trainingsdaten
    train_dataset, test_dataset = train_test_split(dataset, train_size = 0.9, shuffle = True)

    #Gewicht, da non-fractured und fractured nicht gleich viele. Wird übergeben in model
    gewicht = round(((dataset['fractured'].value_counts()).get(0,1))/(dataset['fractured'].value_counts()).get(1,0),3)

    return train_dataset, test_dataset,gewicht


#Todo k-fold cross validation einbauen
def create_generators(train_df,test_df,targetsize):
    """
    Creates a training image dataset and a validation image dataset. Args[df: preprocessed dataframe]
    """
    #Pfad zu Bildern
    path = os.path.join(os.getcwd(),'Dataset_FracAtlas','images','all')

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale = 1./255
                                                              ,horizontal_flip=True
                                                              ,rotation_range=10 
                                                              ,width_shift_range=0.05
                                                              ,height_shift_range=0.05
                                                              ,zoom_range=0.1
                                                              ,validation_split=0.2)
    
    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1./255)


    train_generator = datagen.flow_from_dataframe(dataframe=train_df,
                                                        directory=path,
                                                        x_col='image_id',
                                                        y_col='fractured',
                                                        class_mode='binary',
                                                        color_mode = 'rgb',
                                                        shuffle=True,
                                                        target_size=targetsize,
                                                        subset='training'
                                                        ,batch_size=16)
    
    validation_generator = datagen.flow_from_dataframe(dataframe=train_df,
                                                        directory=path,
                                                        x_col='image_id',
                                                        y_col='fractured',
                                                        class_mode='binary',
                                                        color_mode = 'rgb',
                                                        shuffle=True,
                                                        target_size=targetsize,
                                                        subset='validation'
                                                        ,batch_size=16)

    test_generator = test_datagen.flow_from_dataframe(dataframe=test_df,
                                                      directory=path,
                                                        x_col='image_id',
                                                        y_col='fractured',
                                                        class_mode='binary',
                                                        color_mode = 'rgb',
                                                        shuffle=True,
                                                        target_size=targetsize,
                                                        batch_size=16)

    
    return train_generator, validation_generator, test_generator



    

def main():
    train_dataset, test_dataset, gewicht = preprocessing(general_info_df)

    
    targetsize = (224,224)
    train_generator,validation_generator, test_generator = create_generators(train_dataset,test_dataset,targetsize)

    InceptionV3(train_generator,validation_generator,test_generator,gewicht)
    #showimage('IMG0003726.jpg')

if __name__ == "__main__":
    main()