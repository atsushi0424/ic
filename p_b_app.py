import cv2
from PIL import Image, ImageOps
import numpy as np
import tensorflow as tf
import streamlit as st

model = tf.keras.models.load_model("my_model_p_b.hdf5")
st.write(
    """
         # Putin-Biden Prediction
         """
)
st.write("This is a simple image classification web app to predict Putin and Biden")
_file = st.file_uploader("Please upload an image file", type=["jpg", "png"])


def import_and_predict(image_data, model):
    size = (150, 150)
    image = ImageOps.fit(image_data, size, Image.ANTIALIAS)
    image = np.asarray(image)
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_resize = (
        cv2.resize(img, dsize=(75, 75), interpolation=cv2.INTER_CUBIC)
    ) / 255.0

    img_reshape = img_resize[np.newaxis, ...]

    prediction = model.predict(img_reshape)

    return prediction


if _file is None:
    st.text("Please upload an image file")
else:
    image = Image.open(_file)
    st.image(image, use_column_width=True)
    prediction = import_and_predict(image, model)

    if np.argmax(prediction) == 0:
        st.write("He must be Biden!")
    elif np.argmax(prediction) == 1:
        st.write("He must be Putin")

    st.text("Probability (0: Biden, 1: Putin)")
    st.write(prediction)
