import keras_vggface
import keras_vggface.utils
import matplotlib as mpl
import numpy as np
import tensorflow as tf
from keras.layers import Dense, Flatten, Input
from keras.utils.data_utils import get_file
from keras_vggface.vggface import VGGFace
from tensorflow import keras
import matplotlib.pyplot as plt

class FaceRecognitionModel:
    def __init__(self, num_classes, image_size=(224, 224), batch_size=8, learning_rate=0.0001, epochs=20):
        self.image_size = image_size
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.learning_rate = learning_rate
        self.epochs = epochs

    def load_dataset(self, directory):
        return keras.utils.image_dataset_from_directory(
            directory, shuffle=True, image_size=self.image_size, batch_size=self.batch_size
        )

    def data_augmentation(self):
        return keras.Sequential([
            keras.layers.RandomFlip("horizontal"),
            keras.layers.RandomRotation(0.2),
        ])

    def build_model(self):
        base = VGGFace(model='resnet50', include_top=False, input_shape=(*self.image_size, 3))
        base.trainable = False
        last_layer = base.get_layer('avg_pool').output

        inputs = tf.keras.Input(shape=(*self.image_size, 3))

        x = self.data_augmentation()(inputs)
        x = base(x)
        x = Flatten(name='flatten')(x)

        out = Dense(self.num_classes, name='classifier')(x)

        custom_model = keras.Model(inputs, out)
        custom_model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=['accuracy']
        )

        return custom_model

    def train(self, dataset_directory):
        train_dataset = self.load_dataset(dataset_directory)
        custom_model = self.build_model()
        history = custom_model.fit(train_dataset, epochs=self.epochs)
        return history
    


if __name__ == "__main__":
    model = FaceRecognitionModel(num_classes=4)
    history = model.train("./Faces")

    plt.plot(history.history['accuracy'])
    plt.plot(history.history['loss'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.show()


