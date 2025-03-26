import tensorflow as tf
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D

# Load Fashion-MNIST or custom dataset
model = tf.keras.applications.MobileNetV2(weights=None, input_shape=(224, 224, 3))
model.compile(optimizer="adam", loss="categorical_crossentropy")
model.fit(train_images, train_labels, epochs=10)
model.save("clothing_classifier")