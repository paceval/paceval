In this project, a Neural Network is trained to classify geometric shapes in pictures. 
The Neural Network predicts the probability that a specific shape is in a picture. The shapes used are Triangles, Squares, Stars, and Circles.
The training of the Network is done in the notebook "train_nn.ipynb" and involves the usage of a custom class "NN_class.py", 
that defines the architecture and methods of the Neural Network. The final weights are stored in the folder "model_weights".
The training data consists of four CSV's and is stored in "shapes_processed_20".

After training the Neural Network can be transformed/exported into closed mathematical functions using paceval. 
This process is done in the Julia Notebook "create_formulas.ipynb". Here the weights are loaded from "model_weights" to be able to use the same Model in 
Julia. The created formulas are stored in the folder "formulas".

To evaluate and use the created formulas we use the python libary of paceval in the python notebook "evaluate_formulas.ipynb". Here the formulas are applied
to a custom use case, that works by using the calculated probabilities of the formulas. The custom file "evaluation_class.py" is also used in the notebook.

Copyright © 2015-2026 paceval.® All rights reserved.<br>
mailto:info@paceval.com

