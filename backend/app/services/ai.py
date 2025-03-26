import tensorflow as tf
from PIL import Image

model = tf.keras.models.load_model("../ml/clothing_classifier")

def tag_clothing(image_path: str) -> dict:
    img = Image.open(image_path).resize((224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    prediction = model.predict(np.expand_dims(img_array, axis=0))
    return {"type": prediction["type"], "weight": prediction["weight"]}